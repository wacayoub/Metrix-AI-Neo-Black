package main

import (
	"crypto/ecdh"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"io"
	"net/http"
	"net/http/httptest"
	"net/netip"
	"net/url"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"golang.zx2c4.com/wireguard/conn"
	"golang.zx2c4.com/wireguard/device"
	"golang.zx2c4.com/wireguard/tun/netstack"
)

func newKey(t *testing.T) *ecdh.PrivateKey {
	t.Helper()
	k, err := ecdh.X25519().GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal("key fixture failed")
	}
	return k
}

func fixture(t *testing.T) (*Endpoint, *http.Client, string, Peer) {
	t.Helper()
	serverKey, clientKey := newKey(t), newKey(t)
	web := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, "neo-fixture") }))
	t.Cleanup(web.Close)
	u, _ := url.Parse(web.URL)
	port, _ := strconv.Atoi(u.Port())
	peer := Peer{base64.StdEncoding.EncodeToString(clientKey.PublicKey().Bytes()), "10.78.0.2/32"}
	ep, err := startEndpoint(Message{PrivateKey: base64.StdEncoding.EncodeToString(serverKey.Bytes()), ReceiverHost: "192.168.11.2", ReceiverPort: port, Peers: []Peer{peer}}, 0)
	if err != nil {
		t.Fatal("endpoint fixture failed:", err)
	}
	t.Cleanup(ep.Close)
	config, _ := ep.dev.IpcGet()
	listen := ""
	for _, line := range strings.Split(config, "\n") {
		if strings.HasPrefix(line, "listen_port=") {
			listen = strings.TrimPrefix(line, "listen_port=")
		}
	}
	if listen == "" || listen == "0" {
		t.Fatal("no UDP socket")
	}
	tun, clientNet, err := netstack.CreateNetTUN([]netip.Addr{netip.MustParseAddr("10.78.0.2")}, nil, 1380)
	if err != nil {
		t.Fatal("client fixture failed")
	}
	clientDev := device.NewDevice(tun, conn.NewDefaultBind(), device.NewLogger(device.LogLevelSilent, ""))
	t.Cleanup(clientDev.Close)
	err = clientDev.IpcSet("private_key=" + hex.EncodeToString(clientKey.Bytes()) + "\npublic_key=" + hex.EncodeToString(serverKey.PublicKey().Bytes()) +
		"\nendpoint=127.0.0.1:" + listen + "\nallowed_ip=192.168.11.2/32\npersistent_keepalive_interval=1\n")
	if err != nil {
		t.Fatal("client config fixture failed")
	}
	if err := clientDev.Up(); err != nil {
		t.Fatal("client fixture unavailable")
	}
	transport := &http.Transport{DialContext: clientNet.DialContext, DisableKeepAlives: true}
	t.Cleanup(transport.CloseIdleConnections)
	client := &http.Client{Transport: transport, Timeout: 2 * time.Second}
	return ep, client, "http://192.168.11.2:" + strconv.Itoa(port), peer
}

func getFixture(t *testing.T, client *http.Client, target string) {
	t.Helper()
	response, err := client.Get(target)
	if err != nil {
		t.Fatal("encrypted fixture request failed:", err)
	}
	defer response.Body.Close()
	data, _ := io.ReadAll(response.Body)
	if response.StatusCode != 200 || string(data) != "neo-fixture" {
		t.Fatal("invalid fixture response")
	}
}

func TestAuthenticatedWireGuardReachesOnlyConfiguredLocalService(t *testing.T) {
	_, client, target, _ := fixture(t)
	getFixture(t, client, target)
	var unexpected atomic.Int32
	other := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { unexpected.Add(1) }))
	defer other.Close()
	u, _ := url.Parse(other.URL)
	response, err := client.Get("http://192.168.11.2:" + u.Port())
	if response != nil {
		response.Body.Close()
	}
	if err == nil || unexpected.Load() != 0 {
		t.Fatal("unconfigured host port was reachable")
	}
}

func TestAddingAnotherPeerKeepsExistingSession(t *testing.T) {
	ep, client, target, peer := fixture(t)
	getFixture(t, client, target)
	other := newKey(t)
	if err := ep.Update([]Peer{peer, {base64.StdEncoding.EncodeToString(other.PublicKey().Bytes()), "10.78.0.3/32"}}); err != nil {
		t.Fatal(err)
	}
	getFixture(t, client, target)
}

func TestRevokedPeerNoLongerReachesService(t *testing.T) {
	ep, client, target, _ := fixture(t)
	getFixture(t, client, target)
	if err := ep.Update(nil); err != nil {
		t.Fatal(err)
	}
	response, err := client.Get(target)
	if response != nil {
		response.Body.Close()
	}
	if err == nil {
		t.Fatal("revoked peer retained access")
	}
}

func TestPeerRoutesAndKeysAreRestricted(t *testing.T) {
	k := base64.StdEncoding.EncodeToString(newKey(t).PublicKey().Bytes())
	for _, peers := range [][]Peer{
		{{k, "0.0.0.0/0"}}, {{k, "10.78.0.2/24"}}, {{k, "10.78.0.1/32"}},
		{{k, "10.78.0.10/32"}}, {{"invalid", "10.78.0.2/32"}}, {{k, "10.78.0.2/32"}, {k, "10.78.0.3/32"}},
	} {
		if _, err := checkedPeers(peers); err == nil {
			t.Fatal("unrestricted peer accepted")
		}
	}
	if privateIPv4("8.8.8.8") || privateIPv4("127.0.0.1") || privateIPv4("10.78.0.5") || !privateIPv4("192.168.11.2") {
		t.Fatal("receiver policy failed")
	}
}
