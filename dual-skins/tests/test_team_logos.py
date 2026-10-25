"""EPG identities, external-provider failures, bounded cache and late replies."""
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import Mock, patch

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"runtime"),str(ROOT/"plugin")]
from Components.MetrixNEO.settings import DEFAULTS, validate
from Components.MetrixNEO.teams import match_pair, event_snapshot, team_key
from MetrixNEOHelper.cache import Cache
from MetrixNEOHelper import club_logos as provider, service


def event(title="Real Madrid – FC Barcelone",start=100):
    return types.SimpleNamespace(getEventName=lambda:title,getBeginTime=lambda:start,
        getShortDescription=lambda:"La Liga · Football",getExtendedDescription=lambda:"")


def row(name="Real Madrid",identity="133738",**extra):
    return dict(strTeam=name,idTeam=identity,strSport="Soccer",
                strBadge="https://r2.thesportsdb.com/images/media/team/badge/"+identity+".png",**extra)


class TeamNames(unittest.TestCase):
    def test_explicit_pairs_and_french_aliases(self):
        for title in ("Real Madrid - FC Barcelone","Football : Real Madrid vs FC Barcelone","[LIVE] Real Madrid / FC Barcelone"):
            pair=match_pair(title)
            self.assertEqual(tuple(map(team_key,pair)),("real madrid","barcelona"))
        self.assertEqual(team_key("Paris SG"),team_key("PSG"))

    def test_short_description_can_supply_the_pair(self):
        self.assertEqual(match_pair("La Liga","Real Madrid – Barcelona"),("Real Madrid","Barcelona"))

    def test_reserve_women_and_hyphenated_names_remain_distinct(self):
        self.assertNotEqual(team_key("Barcelona B"),team_key("Barcelona"))
        self.assertNotEqual(team_key("Barcelona Women"),team_key("Barcelona"))
        self.assertEqual(match_pair("Paris Saint-Germain – Lyon"),("Paris Saint-Germain","Lyon"))

    def test_ambiguous_pairs_other_sports_and_missing_separator_hide(self):
        for title,short in (("Football", ""),("Real Madrid Barcelona", ""),("Real Madrid - Barcelona - Lyon", ""),("Real Madrid - Barcelona", "Basketball"),("Real Madrid - Barcelona\nArsenal - Chelsea", "")):
            self.assertIsNone(match_pair(title,short))

    def test_clear_title_has_priority_over_historical_summary(self):
        self.assertEqual(match_pair("Real Madrid - Barcelona","Football","Arsenal - Chelsea"),("Real Madrid","Barcelona"))

    def test_snapshot_contains_no_native_event_or_service_object(self):
        key,names=event_snapshot(event())
        self.assertEqual(key,("Real Madrid – FC Barcelone",100))
        self.assertEqual(names,("Real Madrid","FC Barcelone"))
        self.assertIsNone(event_snapshot(event(start=0)))
        self.assertIsNone(event_snapshot(None))

    def test_network_and_logos_are_separate_opt_ins(self):
        self.assertFalse(DEFAULTS["club_logos"])
        self.assertFalse(DEFAULTS["club_network_consent"])
        self.assertEqual(validate({"club_logos":True})["sports_api_key"],"123")
        for key in ("https://example.com","../123","","123\n","١٢٣"):
            with self.assertRaises(ValueError):validate({"sports_api_key":key})


class ProviderAndCache(unittest.TestCase):
    def setUp(self):
        path=ROOT/"build/test-tmp";path.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=path);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/"teams"
        self.now=[100]
        self.cache=Cache(self.root,clock=lambda:self.now[0])
        self.settings=dict(DEFAULTS,club_logos=True,club_network_consent=True)
        stream=io.BytesIO();Image.new("RGBA",(16,16),(0,0,0,0)).save(stream,"PNG")
        self.png=stream.getvalue()

    def network(self,url,limit):
        if "searchteams.php" in url:
            name=parse_qs(urlsplit(url).query)["t"][0]
            return json.dumps({"teams":[row("Real Madrid","1") if name=="real madrid" else row("Barcelona","2")]}).encode()
        return self.png

    def test_only_exact_unambiguous_soccer_identity_is_accepted(self):
        self.assertIsNone(provider.select_team({"teams":[row("Real Madrid B")]},"Real Madrid"))
        self.assertIsNone(provider.select_team({"teams":[row(identity="1"),row(identity="2")]},"Real Madrid"))
        self.assertIsNone(provider.select_team({"teams":[dict(row(),strSport="Basketball")]},"Real Madrid"))
        result=provider.select_team({"teams":[row("Barcelona")]},"FC Barcelone")
        self.assertEqual(result["name"],"Barcelona")

    def test_offline_without_cache_does_not_touch_network_or_create_files(self):
        with patch.object(provider,"read_url") as network:
            self.assertIsNone(provider.team_badge("Real Madrid",dict(self.settings,club_network_consent=False),self.cache))
            network.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_pair_download_is_cached_and_reused_even_offline_after_ttl(self):
        with patch.object(provider,"read_url",side_effect=self.network) as network:
            pair=provider.resolve_pair(("Real Madrid","FC Barcelone"),self.settings,self.cache)
            self.assertEqual(set(pair),{"home","away"})
            self.assertEqual(network.call_count,4)
            for path in pair.values():self.assertEqual(Path(path).read_bytes(),self.png)
            self.assertEqual(provider.resolve_pair(("Real Madrid","FC Barcelone"),self.settings,self.cache),pair)
            self.now[0]+=self.settings["poster_ttl"]+1
            self.assertEqual(provider.resolve_pair(("Real Madrid","FC Barcelone"),dict(self.settings,club_network_consent=False),self.cache),pair)
            self.assertEqual(network.call_count,4)

    def test_missing_or_ambiguous_team_is_negative_cached(self):
        with patch.object(provider,"read_url",return_value=b'{"teams":null}') as network:
            for unused in range(2):self.assertIsNone(provider.team_badge("Unknown",self.settings,self.cache))
            self.assertEqual(network.call_count,1)

    def test_provider_outage_uses_previous_valid_image(self):
        with patch.object(provider,"read_url",side_effect=self.network):
            original=provider.team_badge("Real Madrid",self.settings,self.cache)
        self.now[0]+=self.settings["poster_ttl"]+1
        with patch.object(provider,"read_url",side_effect=OSError("offline")):
            self.assertEqual(provider.team_badge("Real Madrid",self.settings,self.cache)["path"],original["path"])

    def test_external_local_or_insecure_badge_urls_are_rejected(self):
        for url in ("http://www.thesportsdb.com/a.png","https://evil.example/a.png","https://www.thesportsdb.com.evil.example/a.png","https://127.0.0.1/a.png","https://user@www.thesportsdb.com/a.png","https://www.thesportsdb.com:9000/a.png"):
            self.assertFalse(provider.allowed_url(url))
            with self.assertRaises(ValueError):provider.read_url(url,100)
        redirect=provider.ProviderRedirect()
        with self.assertRaises(ValueError):redirect.redirect_request(None,None,302,"",{},"https://example.org/a.png")

    def test_download_timeout_and_size_are_bounded(self):
        response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        response.geturl.return_value="https://www.thesportsdb.com/a.png"
        response.read.return_value=b"abc"
        opener=Mock();opener.open.return_value=response
        with patch.object(provider,"build_opener",return_value=opener):
            self.assertEqual(provider.read_url(response.geturl(),10),b"abc")
            self.assertEqual(opener.open.call_args.kwargs["timeout"],5)
            response.read.assert_called_once_with(11)
            with self.assertRaises(ValueError):provider.read_url(response.geturl(),2)

    def test_invalid_oversized_or_partial_pair_never_reaches_display(self):
        self.assertFalse(provider.png_badge(b"<html>failure</html>"))
        large=bytearray(self.png);large[16:20]=(2000).to_bytes(4,"big")
        self.assertFalse(provider.png_badge(large))
        with patch.object(provider,"team_badge",side_effect=[dict(id="1",path="a.png"),None]):
            self.assertIsNone(provider.resolve_pair(("A","B"),self.settings,self.cache))
        with patch.object(provider,"team_badge",return_value=dict(id="1",path="a.png")):
            self.assertIsNone(provider.resolve_pair(("A","B"),self.settings,self.cache))

    def test_binary_and_json_share_budget_preserving_unowned_files(self):
        self.root.mkdir()
        sentinel=self.root/"user.png";sentinel.write_bytes(b"preserve")
        cache=Cache(self.root,max_bytes=230)
        for i in range(5):
            cache.put_image(str(i),self.png)
            cache.put(str(i),{"team":i},100)
        self.assertLessEqual(sum(p.stat().st_size for p in self.root.glob("neo-*.*")),230)
        self.assertEqual(sentinel.read_bytes(),b"preserve")


class BackgroundQueue(unittest.TestCase):
    def setUp(self):
        self.jobs=[]
        owner=self
        class Deferred:
            def addCallbacks(self,success,failure):
                self.success,self.failure=success,failure
                return self
        def defer(function,*args):
            task=Deferred();owner.jobs.append((function,args,task));return task
        reactor=types.SimpleNamespace(callLater=Mock(return_value=object()))
        internet=types.ModuleType("twisted.internet");internet.reactor=reactor
        threads=types.ModuleType("twisted.internet.threads");threads.deferToThread=defer
        modules=patch.dict(sys.modules,{"twisted.internet":internet,"twisted.internet.threads":threads})
        modules.start();self.addCleanup(modules.stop)
        self.reactor=reactor;self.now=[100]
        state=patch.multiple(service,_state={},_club_listeners={},_auto_clubs={},_club_seen={},_club_pending={},_club_active=False,_club_due=0,_club_timer=None,time=lambda:self.now[0])
        state.start();self.addCleanup(state.stop)
        self.settings=dict(DEFAULTS,club_logos=True,club_network_consent=True)

    def test_home_and_away_deduplicate_and_refresh_without_ui_io(self):
        listener=type("Listener",(),{"CHANGED_ALL":1,"changed":Mock()})()
        service.watch_clubs("MetrixNEO",listener)
        with patch.object(service,"Cache",side_effect=AssertionError("UI disk access")):
            service.request_clubs(event(),"MetrixNEO",self.settings)
            service.request_clubs(event(),"MetrixNEO",self.settings)
        self.assertEqual(len(self.jobs),1)
        self.assertEqual(self.jobs[0][1][1],("Real Madrid","FC Barcelone"))
        self.assertIsNone(service.club_path(event(),"MetrixNEO","home"))
        self.jobs[0][2].success({"home":"home.png","away":"away.png"})
        self.assertEqual(service.club_path(event(),"MetrixNEO","away"),"away.png")
        listener.changed.assert_called_once_with((1,))
        self.assertFalse(service._club_pending)
        self.reactor.callLater.assert_not_called()

    def test_late_reply_cannot_supply_logos_to_another_event(self):
        first,second=event(),event("Arsenal - Chelsea",200)
        service.request_clubs(first,"MetrixNEO",self.settings)
        service.request_clubs(second,"MetrixNEO",self.settings)
        self.jobs[0][2].success({"home":"old-home.png","away":"old-away.png"})
        self.assertIsNone(service.club_path(second,"MetrixNEO","home"))
        self.assertEqual(self.reactor.callLater.call_args.args[0],20)
        self.now[0]=120;self.reactor.callLater.call_args.args[1]()
        self.assertEqual(len(self.jobs),2)
        self.jobs[1][2].success({"home":"new-home.png","away":"new-away.png"})
        self.assertEqual(service.club_path(second,"MetrixNEO","home"),"new-home.png")

    def test_disabled_unparsed_or_failed_events_do_not_retry_on_every_redraw(self):
        service.request_clubs(event(),"MetrixNEO",DEFAULTS)
        service.request_clubs(event("News"),"MetrixNEO",self.settings)
        self.assertFalse(self.jobs)
        service.request_clubs(event(),"MetrixNEO",self.settings)
        self.jobs[0][2].failure(object())
        for unused in range(5):service.request_clubs(event(),"MetrixNEO",self.settings)
        self.assertEqual(len(self.jobs),1)

    def test_profile_snapshots_and_manual_pairs_are_preserved(self):
        key=event_snapshot(event())[0]
        service._auto_clubs["MetrixNEO"]={key:{"home":"auto-home","away":"auto-away","teams":("real madrid","barcelona")}}
        service._state["MetrixNEO"]={"clubs":{"home":{key:"local-home"},"away":{key:"local-away"}}}
        self.assertEqual(service.club_path(event(),"MetrixNEO","home"),"local-home")
        self.assertIsNone(service.club_path(event(),"MetrixNEOAdvanced","home"))
        service.refresh("MetrixNEO")
        self.jobs[0][2].success({"settings":self.settings,"clubs":{}})
        self.assertEqual(service.club_path(event(),"MetrixNEO","home"),"auto-home")
        self.assertEqual(service.settings_for("MetrixNEO",{}),self.settings)

    def test_changed_names_under_same_event_title_reject_old_pair(self):
        current=event("Football",100)
        current.getShortDescription=lambda:"Real Madrid - Barcelona"
        service.request_clubs(current,"MetrixNEO",self.settings)
        self.jobs[0][2].success({"home":"old-home","away":"old-away"})
        self.assertEqual(service.club_path(current,"MetrixNEO","home"),"old-home")
        current.getShortDescription=lambda:"Arsenal - Chelsea"
        self.assertIsNone(service.club_path(current,"MetrixNEO","home"))
        service.request_clubs(current,"MetrixNEO",self.settings)
        self.assertTrue(service._club_pending)

    def test_disabling_automatic_logos_hides_cached_pair_but_keeps_manual(self):
        current=event()
        service.request_clubs(current,"MetrixNEO",self.settings)
        self.jobs[0][2].success({"home":"auto-home","away":"auto-away"})
        service._state["MetrixNEO"]={"settings":dict(self.settings,club_logos=False,posters=True)}
        self.assertIsNone(service.club_path(current,"MetrixNEO","home"))
