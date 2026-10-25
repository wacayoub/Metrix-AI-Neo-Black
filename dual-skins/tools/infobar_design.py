"""Two independent infobars traced from 1000515121 and 1000515120."""
from generate_skins import sub, widget, rect, screen


def text(parent, profile, mode, pos, size, font=24, source="session.CurrentService", **attrs):
    attrs.setdefault("foregroundColor", "infobar_ink")
    return widget(parent, pos, size, source=source, converters=[("MetrixNEOInfo", mode + "," + profile)], font=font, **attrs)


def picture(parent, profile, name, pos, size):
    sub(parent, "ePixmap", position=pos, size=size, pixmap=profile + "/assets/" + name + ".png", alphatest="blend", scale="scale")


def state_icon(parent, profile, kind, mode, pos, size, source="session.CurrentService"):
    return widget(parent,pos,size,source=source,render="MetrixNEOInfobarIcon",neoProfile=profile,neoKind=kind,scale="scale",alphatest="blend",converters=[("MetrixNEOInfo",mode+","+profile)])


def header(parent, profile):
    advanced = profile.endswith("Advanced")
    x, y, width, height = (36, 24, 744, 104) if advanced else (30, 24, 652, 124)
    picture(parent, profile, "infobar-weather", f"{x},{y}", f"{width},{height}")
    text(parent, profile, "WeatherLocation", f"{x+18},{y+10}", "220,28", 21, source="global.CurrentTime")
    text(parent, profile, "WeatherTemperatureCompact" if advanced else "WeatherTemperature", f"{x+18},{y+40}", "130,51", 43, source="global.CurrentTime")
    if advanced:
        widget(parent, f"{x+116},{y+37}", "56,55", source="global.CurrentTime", render="MetrixNEOWeather", neoProfile=profile, neoDay="-1", neoInfobar="1", scale="centerScaled")
        text(parent, profile, "WeatherTodayLabel", f"{x+184},{y+36}", "130,25", 17, source="global.CurrentTime")
        text(parent, profile, "WeatherTodayRange", f"{x+184},{y+67}", "130,25", 17, source="global.CurrentTime")
        for i in range(3):
            px=x+320+i*145
            rect(parent,f"{px-16},{y+14}","1,78","line")
            text(parent,profile,f"WeatherDay{i+1}",f"{px},{y+7}","66,25",19,source="global.CurrentTime")
            widget(parent,f"{px-4},{y+35}","57,53",source="global.CurrentTime",render="MetrixNEOWeather",neoProfile=profile,neoDay=str(i),scale="centerScaled")
            text(parent,profile,f"WeatherHigh{i+1}",f"{px+63},{y+33}","54,26",18,source="global.CurrentTime")
            text(parent,profile,f"WeatherLow{i+1}",f"{px+63},{y+65}","54,26",18,source="global.CurrentTime",foregroundColor="muted")
    else:
        text(parent, profile, "WeatherCondition", f"{x+18},{y+91}", "232,26", 19, source="global.CurrentTime")
        widget(parent, f"{x+145},{y+28}", "87,81", source="global.CurrentTime", render="MetrixNEOWeather", neoProfile=profile, neoDay="-1", neoInfobar="1", scale="centerScaled")
        for i in range(3):
            px=x+275+i*124
            rect(parent,f"{px-12},{y+14}","1,94","line")
            text(parent,profile,f"WeatherDay{i+2}",f"{px},{y+8}","106,26",20,source="global.CurrentTime",halign="center")
            widget(parent,f"{px+25},{y+33}","53,49",source="global.CurrentTime",render="MetrixNEOWeather",neoProfile=profile,neoDay=str(i+1),scale="centerScaled")
            text(parent,profile,f"WeatherRange{i+2}",f"{px-4},{y+78}","114,28",20,source="global.CurrentTime",halign="center")
    cx, cw, ch = (1530, 354, 94) if advanced else (1572, 318, 118)
    picture(parent, profile, "infobar-clock", f"{cx},24", f"{cw},{ch}")
    if advanced:
        widget(parent, f"{cx+14},37", "135,65", source="global.CurrentTime", converters=[("ClockToText", "Format:%A\n%d %B")], font=20, halign="center")
        rect(parent, f"{cx+161},39", "1,62", "line")
        widget(parent, f"{cx+176},39", "166,64", source="global.CurrentTime", converters=[("ClockToText", "Format:%H:%M")], font=58, halign="center")
    else:
        widget(parent, f"{cx+10},37", "298,29", source="global.CurrentTime", converters=[("ClockToText", "Format:%A %d %B %Y")], font=21, halign="center")
        widget(parent, f"{cx+30},67", "266,65", source="global.CurrentTime", converters=[("ClockToText", "Format:%H:%M")], font=62, halign="right")


def event(parent, source, mode, pos, size, font=25, **attrs):
    attrs.setdefault("foregroundColor", "infobar_ink")
    converters = [("EventName", mode)] if mode in ("Name", "ShortDescription") else [("EventTime", mode), ("ClockToText", "Format:%H:%M")]
    return widget(parent, pos, size, source=source, converters=converters, font=font, **attrs)


def technical_row(parent, profile, advanced):
    # Each measured field owns a column. Missing or long values never move the
    # neighbours. Text, badges and rules share the same optical centre line.
    columns = (("Resolution",545,130),("FrameRate",691,90),("Aspect",797,57),
               ("Audio",869,74),("Language",959,65),("Orbital",1040,113),
               ("Tuning",1169,305)) if advanced else (
               ("Resolution",590,130),("FrameRate",736,90),("Aspect",842,54),
               ("Audio",912,67),("Language",995,67),("Tuning",1230,172))
    y = 1000 if advanced else 999
    for index,(mode,x,width) in enumerate(columns):
        if index:
            rect(parent,f"{x-8},{y+6}","1,22","infobar_line")
        text(parent,profile,"Technical"+mode,f"{x},{y}",f"{width},34",19,
             noWrap="1",valign="center",foregroundColor="infobar_muted")


def build(root, profile):
    advanced = profile.endswith("Advanced")
    main = screen(root, "InfoBar", bg="transparent")
    header(main, profile)
    # Bottom edge remains exactly 1080. Upper information row / lower status row.
    rect(main, "0,832", "1920,248", "background")
    picture(main, profile, "infobar-strip", "0,832", "1920,248")
    rect(main, "0,832", "1920,2", "infobar_cyan")
    rect(main, "24,978", "1872,1", "line")
    if advanced:
        ppos, psize, npos = "33,866", "140,88", "242,870"
        rect(main, "199,859", "1,108", "line_bright")
        widget(main, "320,878", "264,43", source="session.CurrentService", converters=[("ServiceName", "Name")], font=29)
        text(main, profile, "BadgeResolution", "595,878", "58,36", 26, foregroundColor="yellow")
        for role, x in (("home", 675), ("away", 744)):
            widget(main, f"{x},854", "62,74", source="session.Event_Now", render="MetrixNEOPoster", neoProfile=profile, neoRole=role)
        title_x, title_w, prog_x, prog_w = 822, 536, 750, 750
        event(main, "session.Event_Now", "ShortDescription", "822,898", "520,32", 21, foregroundColor="muted", noWrap="1")
        text(main, profile, "Smart", "1140,941", "350,30", 21, source="session.Event_Now", halign="right", foregroundColor="accent")
        next_x, next_width = 1640, 250
        state_icon(main,profile,"record","Record","1362,860","30,30",source="session.RecordState")
        text(main, profile, "RecordLabel", "1398,863", "60,30", 18, source="session.RecordState", foregroundColor="red")
        state_icon(main,profile,"timeshift","TimeshiftCompact","1460,858","33,33")
        text(main, profile, "TimeshiftCompact", "1503,863", "122,30", 18, foregroundColor="muted")
        start_pos, end_pos = "674,938", "1516,938"
    else:
        ppos, psize, npos = "158,861", "120,91", "38,878"
        widget(main, "80,706", "1760,124", source="session.CurrentService",
               converters=[("ServiceName", "Name")], font="ChannelLight;112",
               foregroundColor="infobar_ink", halign="left", valign="bottom", noWrap="1")
        rect(main, "136,861", "1,95", "line")
        rect(main, "298,854", "1,104", "line")
        title_x, title_w, prog_x, prog_w = 320, 740, 404, 475
        event(main, "session.Event_Now", "ShortDescription", "320,900", "730,32", 23, foregroundColor="muted", noWrap="1")
        rect(main, "1075,855", "1,104", "line_bright")
        for role, x in (("home", 1115), ("away", 1300)):
            widget(main, f"{x},855", "88,104", source="session.Event_Now", render="MetrixNEOPoster", neoProfile=profile, neoRole=role)
        text(main, profile, "Match", "1215,887", "75,45", 30, source="session.Event_Now", halign="center")
        rect(main, "1418,855", "1,104", "line")
        next_x, next_width = 1440, 265
        widget(main, "1722,860", "170,96", source="session.Event_Next", render="MetrixNEOPoster", neoProfile=profile)
        start_pos, end_pos = "320,937", "900,937"
        widget(main, "982,937", "90,32", source="session.Event_Now", converters=[("EventTime", "Remaining"), ("RemainingToText", "OnlyMinute")], font=23, foregroundColor="accent")
    widget(main, ppos, psize, source="session.CurrentService", render="MetrixNEOPicon", converters=[("ServiceName", "Reference")])
    widget(main, npos, "91,60", source="session.CurrentService", converters=[("ServiceName", "Number")], font=44, halign="center")
    event(main, "session.Event_Now", "Name", f"{title_x},850", f"{title_w},45", 29 if advanced else 35, noWrap="1")
    event(main, "session.Event_Now", "StartTime", start_pos, "78,34", 23)
    event(main, "session.Event_Now", "EndTime", end_pos, "88,34", 23)
    widget(main, f"{prog_x},947", f"{prog_w},9", source="session.Event_Now", render="Progress", converters=[("EventTime", "Progress")], foregroundColor="infobar_cyan", backgroundColor="track", borderWidth="0")
    rect(main, f"{next_x-20},855", "1,108", "line")
    text(main, profile, "NextSummary", f"{next_x},858", f"{next_width},104", 22, source="session.Event_Next")
    badges=(("resolution","BadgeResolution",30,60),("hdr","BadgeHDR",108,66),("audio","BadgeAudio",185,104),("codec","BadgeCodec",307,78),("source","SourceShort",420,90)) if advanced else (("resolution","BadgeResolution",36,60),("hdr","BadgeHDR",114,62),("audio","BadgeAudio",195,104),("codec","BadgeCodec",315,74),("lock","BadgeCA",405,54),("source","SourceShort",477,64))
    for kind,mode,x,width in badges:
        state_icon(main,profile,kind,mode,f"{x},992" if advanced else f"{x},990",f"{width},51")
    rect(main,"568,995" if not advanced else "522,996","1,43","infobar_line")
    technical_row(main,profile,advanced)
    if not advanced:
        state_icon(main,profile,"record","Record","1108,997","38,38",source="session.RecordState")
        text(main, profile, "RecordLabel", "1146,999", "66,34", 18, source="session.RecordState", valign="center")
        state_icon(main,profile,"timeshift","Timeshift","1416,997","38,38")
        text(main, profile, "Timeshift", "1461,999", "115,34", 17, valign="center")
        rect(main,"1579,996","1,56","line")
    for index, key in enumerate(("SNR", "AGC")):
        x, y = (1510 + index*200, 1003) if advanced else (1605, 998+index*36)
        text(main, profile, key + "Label", f"{x},{y}", "47,28" if advanced else "53,28", 18, source="session.FrontendStatus", valign="center")
        text(main, profile, key + "Percent", f"{x+52 if advanced else x+205},{y}", "54,28", 18, source="session.FrontendStatus", halign="right", valign="center")
        widget(main, f"{x+116 if advanced else x+61},{y+8}", "70,12" if advanced else "137,12", source="session.FrontendStatus", render="Progress", converters=[("MetrixNEOInfo", key + "," + profile), ("ConditionalShowHide", "")], orientation="orRightToLeft", foregroundColor="infobar_cyan", backgroundColor="track", borderWidth="0", **({"pixmap": profile + "/assets/infobar-signal.png"} if not advanced else {}))
