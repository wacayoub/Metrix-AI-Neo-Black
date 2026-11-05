// Neo Connect userspace endpoint. No host TUN, routes, forwarding or kernel modules.
package main

import (
	"bufio"
	"crypto/ecdh"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/netip"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"golang.zx2c4.com/wireguard/conn"
	"golang.zx2c4.com/wireguard/device"
	"golang.zx2c4.com/wireguard/tun/netstack"
)

type Peer struct {
	PublicKey string `json:"public_key"`
	Address   string `json:"address"`
}

type Message struct {
	Op           string `json:"op"`
	PrivateKey   string `json:"private_key"`
	ReceiverHost string `json:"receiver_host"`
	ReceiverPort int    `json:"receiver_port"`
	Peers        []Peer `json:"peers"`
}

func decodeKey(value string) ([]byte, error) {
	b, err := base64.StdEncoding.DecodeString(value)
	if err != nil || len(b) != 32 || base64.StdEncoding.EncodeToString(b) != value {
		return nil, errors.New("invalid key")
	}
	for _, v := range b {
		if v != 0 {
			return b, nil
		}
	}
	return nil, errors.New("invalid key")
}

func privateIPv4(value string) bool {
	a, err := netip.ParseAddr(value)
	if err != nil || !a.Is4() {
		return false
	}
	for _, subnet := range []string{"192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"} {
		if netip.MustParsePrefix(subnet).Contains(a) {
			return !netip.MustParsePrefix("10.78.0.0/24").Contains(a)
		}
	}
	return false
}

func checkedPeers(peers []Peer) (map[string]string, error) {
	if len(peers) > 8 {
		return nil, errors.New("peer limit")
	}
	keys, addresses := make(map[string]string), make(map[string]bool)
	for _, peer := range peers {
		key, err := decodeKey(peer.PublicKey)
		if err != nil {
			return nil, err
		}
		p, err := netip.ParsePrefix(peer.Address)
		if err != nil || !p.Addr().Is4() || p.Bits() != 32 || !strings.HasPrefix(peer.Address, "10.78.0.") {
			return nil, errors.New("invalid address")
		}
		last := p.Addr().As4()[3]
		k := hex.EncodeToString(key)
		if last < 2 || last > 9 || addresses[peer.Address] {
			return nil, errors.New("invalid address")
		}
		if _, exists := keys[k]; exists {
			return nil, errors.New("duplicate peer")
		}
		addresses[peer.Address], keys[k] = true, peer.Address
	}
	return keys, nil
}

type Endpoint struct {
	dev       *device.Device
	net       *netstack.Net
	listeners []net.Listener
	mu        sync.Mutex
	peers     map[string]string
	active    map[net.Conn]string
	slots     chan struct{}
	closed    bool
}

func startEndpoint(m Message, port int) (*Endpoint, error) {
	if !privateIPv4(m.ReceiverHost) || m.ReceiverPort < 1 || m.ReceiverPort > 65535 {
		return nil, errors.New("invalid receiver")
	}
	private, err := decodeKey(m.PrivateKey)
	if err != nil {
		return nil, err
	}
	if _, err := checkedPeers(m.Peers); err != nil {
		return nil, err
	}
	tun, network, err := netstack.CreateNetTUN([]netip.Addr{netip.MustParseAddr(m.ReceiverHost)}, nil, 1380)
	if err != nil {
		return nil, errors.New("virtual network unavailable")
	}
	ep := &Endpoint{net: network, peers: make(map[string]string), active: make(map[net.Conn]string), slots: make(chan struct{}, 32)}
	ep.dev = device.NewDevice(tun, conn.NewDefaultBind(), device.NewLogger(device.LogLevelSilent, ""))
	if err := ep.dev.IpcSet("private_key=" + hex.EncodeToString(private) + "\nlisten_port=" + strconv.Itoa(port) + "\n"); err != nil {
		ep.Close()
		return nil, errors.New("wireguard configuration failed")
	}
	if err := ep.Update(m.Peers); err != nil {
		ep.Close()
		return nil, err
	}
	ports := map[int]bool{m.ReceiverPort: true, 8001: true, 8002: true}
	for target := range ports {
		listener, err := network.ListenTCP(&net.TCPAddr{IP: net.ParseIP(m.ReceiverHost), Port: target})
		if err != nil {
			ep.Close()
			return nil, errors.New("virtual listener failed")
		}
		ep.listeners = append(ep.listeners, listener)
		go ep.accept(listener, target)
	}
	if err := ep.dev.Up(); err != nil {
		ep.Close()
		return nil, errors.New("wireguard unavailable")
	}
	return ep, nil
}

func (ep *Endpoint) Update(peers []Peer) error {
	next, err := checkedPeers(peers)
	if err != nil {
		return err
	}
	ep.mu.Lock()
	defer ep.mu.Unlock()
	if ep.closed {
		return errors.New("closed")
	}
	var commands strings.Builder
	allowed := make(map[string]bool)
	for _, address := range next {
		allowed[strings.TrimSuffix(address, "/32")] = true
	}
	for key := range ep.peers {
		if _, exists := next[key]; !exists {
			fmt.Fprintf(&commands, "public_key=%s\nremove=true\n", key)
		}
	}
	for key, address := range next {
		if previous, exists := ep.peers[key]; !exists || previous != address {
			fmt.Fprintf(&commands, "public_key=%s\nreplace_allowed_ips=true\nallowed_ip=%s\n", key, address)
		}
	}
	if commands.Len() > 0 {
		if err := ep.dev.IpcSet(commands.String()); err != nil {
			return errors.New("peer update failed")
		}
	}
	for connection, source := range ep.active {
		if !allowed[source] {
			connection.Close()
			delete(ep.active, connection)
		}
	}
	ep.peers = next
	return nil
}

func (ep *Endpoint) accept(listener net.Listener, port int) {
	for {
		remote, err := listener.Accept()
		if err != nil {
			return
		}
		select {
		case ep.slots <- struct{}{}:
			go ep.proxy(remote, port)
		default:
			remote.Close()
		}
	}
}

func (ep *Endpoint) proxy(remote net.Conn, port int) {
	defer func() { remote.Close(); <-ep.slots }()
	source, _, err := net.SplitHostPort(remote.RemoteAddr().String())
	if err != nil {
		return
	}
	ep.mu.Lock()
	allowed := false
	for _, value := range ep.peers {
		if value == source+"/32" {
			allowed = true
		}
	}
	if !allowed || ep.closed {
		ep.mu.Unlock()
		return
	}
	ep.active[remote] = source
	ep.mu.Unlock()
	defer func() { ep.mu.Lock(); delete(ep.active, remote); ep.mu.Unlock() }()
	// Only these fixed loopback ports can be reached. No arbitrary proxy destination.
	local, err := net.DialTimeout("tcp4", net.JoinHostPort("127.0.0.1", strconv.Itoa(port)), 5*time.Second)
	if err != nil {
		return
	}
	defer local.Close()
	done := make(chan struct{})
	go func() { io.Copy(local, remote); local.Close(); close(done) }()
	io.Copy(remote, local)
	remote.Close()
	<-done
}

func (ep *Endpoint) Close() {
	ep.mu.Lock()
	if ep.closed {
		ep.mu.Unlock()
		return
	}
	ep.closed = true
	for connection := range ep.active {
		connection.Close()
	}
	ep.mu.Unlock()
	for _, listener := range ep.listeners {
		listener.Close()
	}
	if ep.dev != nil {
		ep.dev.Close()
	}
}

func serve() int {
	var endpoint *Endpoint
	defer func() {
		if endpoint != nil {
			endpoint.Close()
		}
	}()
	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGTERM, os.Interrupt)
	go func() { <-signals; os.Stdin.Close() }()
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 4096), 16384)
	encoder := json.NewEncoder(os.Stdout)
	for scanner.Scan() {
		var m Message
		var err error
		if json.Unmarshal(scanner.Bytes(), &m) != nil {
			err = errors.New("invalid request")
		} else if m.Op == "configure" && endpoint == nil {
			endpoint, err = startEndpoint(m, 51820)
		} else if m.Op == "peers" && endpoint != nil {
			err = endpoint.Update(m.Peers)
		} else {
			err = errors.New("invalid operation")
		}
		if err != nil {
			encoder.Encode(map[string]bool{"ok": false}) // No raw config or key in error output.
			return 1
		}
		if encoder.Encode(map[string]bool{"ok": true}) != nil {
			return 1
		}
	}
	return 0 // Parent exit closes stdin: no orphan VPN or kernel interface remains.
}

func main() {
	if len(os.Args) != 2 {
		os.Exit(1)
	}
	switch os.Args[1] {
	case "version":
		fmt.Println("NeoConnectEndpoint/1")
	case "keygen":
		key, err := ecdh.X25519().GenerateKey(rand.Reader)
		if err != nil {
			os.Exit(1)
		}
		fmt.Println(base64.StdEncoding.EncodeToString(key.Bytes()))
	case "public-key":
		input, err := io.ReadAll(io.LimitReader(os.Stdin, 128))
		if err != nil {
			os.Exit(1)
		}
		data, err := decodeKey(strings.TrimSpace(string(input)))
		if err != nil {
			os.Exit(1)
		}
		key, err := ecdh.X25519().NewPrivateKey(data)
		if err != nil {
			os.Exit(1)
		}
		fmt.Println(base64.StdEncoding.EncodeToString(key.PublicKey().Bytes()))
	case "serve":
		os.Exit(serve())
	default:
		os.Exit(1)
	}
}
