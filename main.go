package main

import (
	"flag"
	//"fmt"
	"github.com/jproxy/funcs"
	"github.com/jproxy/g"
)

func main() {
	proxyport := flag.String("proxyport", "8080", "proxy listen addr")
	proxyurl := flag.String("proxyurl", "", "proxy url")
	cfg := flag.String("c", "cfg.json", "configuration file")
	flag.Parse()

	g.ParseConfig(*cfg)

	if g.Config().Debug {
		g.InitLog("debug")
	} else {
		g.InitLog("info")
	}
	g.InitRootDir()

	funcs.StartProxy(*proxyport, *proxyurl)
}
