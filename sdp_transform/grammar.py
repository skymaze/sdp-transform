import re


grammar = {
    "v": [{"name": "version", "reg": r"^(\d*)$"}],
    "o": [
        {
            # o=- 20518 0 IN IP4 203.0.113.1
            # NB: sessionId will be a String in most cases because it is huge
            "name": "origin",
            "reg": r"^(\S*) (\d*) (\d*) (\S*) IP(\d) (\S*)",
            "names": [
                "username",
                "sessionId",
                "sessionVersion",
                "netType",
                "ipVer",
                "address",
            ],
            "format": "%s %s %d %s IP%d %s",
        }
    ],
    # default parsing of these only (though some of these feel outdated)
    "s": [{"name": "name"}],
    "i": [{"name": "description"}],
    "u": [{"name": "uri"}],
    "e": [{"name": "email"}],
    "p": [{"name": "phone"}],
    # TODO: this one can actually be parsed properly...
    "z": [{"name": "timezones"}],
    "r": [{"name": "repeats"}],  # TODO: this one can also be parsed properly
    # k: [{}], # outdated thing ignored
    "t": [
        {
            # t=0 0
            "name": "timing",
            "reg": r"^(\d*) (\d*)",
            "names": ["start", "stop"],
            "format": "%d %d",
        }
    ],
    "c": [
        {
            # c=IN IP4 10.47.197.26
            "name": "connection",
            "reg": r"^IN IP(\d) (\S*)",
            "names": ["version", "ip"],
            "format": "IN IP%d %s",
        }
    ],
    "b": [
        {
            # b=AS:4000
            "push": "bandwidth",
            "reg": r"^(TIAS|AS|CT|RR|RS):(\d*)",
            "names": ["type", "limit"],
            "format": "%s:%s",
        }
    ],
    "m": [
        {
            # m=video 51744 RTP/AVP 126 97 98 34 31
            # NB: special - pushes to session
            # TODO: rtp/fmtp should be filtered by the payloads found here?
            "reg": r"^(\w*) (\d*) ([\w/]*)(?: (.*))?",
            "names": ["type", "port", "protocol", "payloads"],
            "format": "%s %d %s %s",
        }
    ],
    "a": [
        {
            # a=rtpmap:110 opus/48000/2
            "push": "rtp",
            "reg": r"^rtpmap:(\d*) ([\w\-.]*)(?:\s*\/(\d*)(?:\s*\/(\S*))?)?",
            "names": ["payload", "codec", "rate", "encoding"],
            "format": lambda o: "rtpmap:%d %s/%s/%s"
            if o.get("encoding") != None
            else ("rtpmap:%d %s/%s" if o.get("rate") != None else "rtpmap:%d %s"),
        },
        {
            # a=fmtp:108 profile-level-id=24;object=23;bitrate=64000
            # a=fmtp:111 minptime=10; useinbandfec=1
            "push": "fmtp",
            "reg": r"^fmtp:(\d*) ([\S| ]*)",
            "names": ["payload", "config"],
            "format": "fmtp:%d %s",
        },
        {
            # a=control:streamid=0
            "name": "control",
            "reg": r"^control:(.*)",
            "format": "control:%s",
        },
        {
            # a=rtcp:65179 IN IP4 193.84.77.194
            "name": "rtcp",
            "reg": r"^rtcp:(\d*)(?: (\S*) IP(\d) (\S*))?",
            "names": ["port", "netType", "ipVer", "address"],
            "format": lambda o: "rtcp:%d %s IP%d %s"
            if o.get("address") != None
            else "rtcp:%d",
        },
        {
            # a=rtcp-fb:98 trr-int 100
            "push": "rtcpFbTrrInt",
            "reg": r"^rtcp-fb:(\*|\d*) trr-int (\d*)",
            "names": ["payload", "value"],
            "format": "rtcp-fb:%s trr-int %d",
        },
        {
            # a=rtcp-fb:98 nack rpsi
            "push": "rtcpFb",
            "reg": r"^rtcp-fb:(\*|\d*) ([\w\-_]*)(?: ([\w\-_]*))?",
            "names": ["payload", "type", "subtype"],
            "format": lambda o: "rtcp-fb:%s %s %s"
            if o.get("subtype") != None
            else "rtcp-fb:%s %s",
        },
        {
            # a=extmap:2 urn:ietf:params:rtp-hdrext:toffset
            # a=extmap:1/recvonly URI-gps-string
            # a=extmap:3 urn:ietf:params:rtp-hdrext:encrypt urn:ietf:params:rtp-hdrext:smpte-tc 25@600/24
            "push": "ext",
            "reg": r"^extmap:(\d+)(?:\/(\w+))?(?: (urn:ietf:params:rtp-hdrext:encrypt))? (\S*)(?: (\S*))?",
            "names": ["value", "direction", "encrypt-uri", "uri", "config"],
            "format": lambda o: "extmap:%d"
            + ("/%s" if o.get("direction") != None else "")
            + (" %s" if o.get("encrypt-uri") != None else "")
            + " %s"
            + (" %s" if o.get("config") != None else ""),
        },
        {
            # a=extmap-allow-mixed
            "name": "extmapAllowMixed",
            "reg": r"^(extmap-allow-mixed)",
        },
        {
            # a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:PS1uQCVeeCFCanVmcjkpPywjNWhcYD0mXXtxaVBR|2^20|1:32
            "push": "crypto",
            "reg": r"^crypto:(\d*) ([\w_]*) (\S*)(?: (\S*))?",
            "names": ["id", "suite", "config", "sessionConfig"],
            "format": lambda o: "crypto:%d %s %s %s"
            if o.get("sessionConfig") != None
            else "crypto:%d %s %s",
        },
        {
            # a=setup:actpass
            "name": "setup",
            "reg": r"^setup:(\w*)",
            "format": "setup:%s",
        },
        {
            # a=connection:new
            "name": "connectionType",
            "reg": r"^connection:(new|existing)",
            "format": "connection:%s",
        },
        {
            # a=msid:0c8b064d-d807-43b4-b434-f92a889d8587 98178685-d409-46e0-8e16-7ef0db0db64a
            "name": "msid",
            "reg": r"^msid:(.*)",
            "format": "msid:%s",
        },
        {
            # a=ptime:20
            "name": "ptime",
            "reg": r"^ptime:(\d*(?:\.\d*)*)",
            "format": lambda o: "ptime:%d" if isinstance(o, int) else "ptime:%g",
        },
        {
            # a=maxptime:60
            "name": "maxptime",
            "reg": r"^maxptime:(\d*(?:\.\d*)*)",
            "format": "maxptime:%d",
        },
        {
            # a=sendrecv
            "name": "direction",
            "reg": r"^(sendrecv|recvonly|sendonly|inactive)",
        },
        {
            # a=ice-lite
            "name": "icelite",
            "reg": r"^(ice-lite)",
        },
        {
            # a=ice-ufrag:F7gI
            "name": "iceUfrag",
            "reg": r"^ice-ufrag:(\S*)",
            "format": "ice-ufrag:%s",
        },
        {
            # a=ice-pwd:x9cml/YzichV2+XlhiMu8g
            "name": "icePwd",
            "reg": r"^ice-pwd:(\S*)",
            "format": "ice-pwd:%s",
        },
        {
            # a=fingerprint:SHA-1 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33
            "name": "fingerprint",
            "reg": r"^fingerprint:(\S*) (\S*)",
            "names": ["type", "hash"],
            "format": "fingerprint:%s %s",
        },
        {
            # a=candidate:0 1 UDP 2113667327 203.0.113.1 54400 typ host
            # a=candidate:1162875081 1 udp 2113937151 192.168.34.75 60017 typ host generation 0 network-id 3 network-cost 10
            # a=candidate:3289912957 2 udp 1845501695 193.84.77.194 60017 typ srflx raddr 192.168.34.75 rport 60017 generation 0 network-id 3 network-cost 10
            # a=candidate:229815620 1 tcp 1518280447 192.168.150.19 60017 typ host tcpfield active generation 0 network-id 3 network-cost 10
            # a=candidate:3289912957 2 tcp 1845501695 193.84.77.194 60017 typ srflx raddr 192.168.34.75 rport 60017 tcpfield passive generation 0 network-id 3 network-cost 10
            "push": "candidates",
            "reg": r"^candidate:(\S*) (\d*) (\S*) (\d*) (\S*) (\d*) typ (\S*)(?: raddr (\S*) rport (\d*))?(?: tcpfield (\S*))?(?: generation (\d*))?(?: network-id (\d*))?(?: network-cost (\d*))?",
            "names": [
                "foundation",
                "component",
                "protocol",
                "priority",
                "ip",
                "port",
                "type",
                "raddr",
                "rport",
                "tcptype",
                "generation",
                "network-id",
                "network-cost",
            ],
            "format": lambda o: "candidate:%s %d %s %d %s %d typ %s"
            + (" raddr %s rport %d" if o.get("raddr") != None else "")
            + (" tcpfield %s" if o.get("tcptype") != None else "")
            + (" generation %d" if o.get("generation") != None else "")
            + (" network-id %d" if o.get("network-id") != None else "")
            + (" network-cost %d" if o.get("network-cost") != None else ""),
        },
        {
            # a=end-of-candidates (keep after the candidates line for readability)
            "name": "endOfCandidates",
            "reg": r"^(end-of-candidates)",
        },
        {
            # a=remote-candidates:1 203.0.113.1 54400 2 203.0.113.1 54401 ...
            "name": "remoteCandidates",
            "reg": r"^remote-candidates:(.*)",
            "format": "remote-candidates:%s",
        },
        {
            # a=ice-options:google-ice
            "name": "iceOptions",
            "reg": r"^ice-options:(\S*)",
            "format": "ice-options:%s",
        },
        {
            # a=ssrc:2566107569 c'name':t9YU8M1UxTF8Y1A1
            "push": "ssrcs",
            "reg": r"^ssrc:(\d*) ([\w_-]*)(?::(.*))?",
            "names": ["id", "attribute", "value"],
            "format": lambda o: "ssrc:%d"
            + (" %s" if o.get("attribute") != None else "")
            + (":%s" if o.get("value") != None else ""),
        },
        {
            # a=ssrc-group:FEC 1 2
            # a=ssrc-group:FEC-FR 3004364195 1080772241
            "push": "ssrcGroups",
            # token-char = %x21 / %x23-27 / %x2A-2B / %x2D-2E / %x30-39 / %x41-5A / %x5E-7E
            "reg": r"^ssrc-group:([\x21\x23\x24\x25\x26\x27\x2A\x2B\x2D\x2E\w]*) (.*)",
            "names": ["semantics", "ssrcs"],
            "format": "ssrc-group:%s %s",
        },
        {
            # a=msid-semantic: WMS Jvlam5X3SX1OP6pn20zWogvaKJz5Hjf9OnlV
            "name": "msidSemantic",
            "reg": r"^msid-semantic:\s?(\w*) (\S*)",
            "names": ["semantic", "token"],
            "format": "msid-semantic: %s %s",  # space after ':' is not accidental
        },
        {
            # a=group:BUNDLE audio video
            "push": "groups",
            "reg": r"^group:(\w*) (.*)",
            "names": ["type", "mids"],
            "format": "group:%s %s",
        },
        {
            # a=rtcp-mux
            "name": "rtcpMux",
            "reg": r"^(rtcp-mux)",
        },
        {
            # a=rtcp-rsize
            "name": "rtcpRsize",
            "reg": r"^(rtcp-rsize)",
        },
        {
            # a=sctpmap:5000 webrtc-datachannel 1024
            "name": "sctpmap",
            "reg": r"^sctpmap:([\w_/]*) (\S*)(?: (\S*))?",
            "names": ["sctpmapNumber", "app", "maxMessageSize"],
            "format": lambda o: "sctpmap:%s %s %s"
            if o.get("maxMessageSize") != None
            else "sctpmap:%s %s",
        },
        {
            # a=x-google-flag:conference
            "name": "xGoogleFlag",
            "reg": r"^x-google-flag:([^\s]*)",
            "format": "x-google-flag:%s",
        },
        {
            # a=rid:1 send max-width=1280;max-height=720;max-fps=30;depend=0
            "push": "rids",
            "reg": r"^rid:([\d\w]+) (\w+)(?: ([\S| ]*))?",
            "names": ["id", "direction", "params"],
            "format": lambda o: "rid:%s %s %s"
            if o.get("params") != None
            else "rid:%s %s",
        },
        {
            # a=imageattr:97 send [x=800,y=640,sar=1.1,q=0.6] [x=480,y=320] recv [x=330,y=250]
            # a=imageattr:* send [x=800,y=640] recv *
            # a=imageattr:100 recv [x=320,y=240]
            "push": "imageattrs",
            "reg": re.compile(
                # a=imageattr:97
                r"^imageattr:(\d+|\*)"
                +
                # send [x=800,y=640,sar=1.1,q=0.6] [x=480,y=320]
                r"[\s\t]+(send|recv)[\s\t]+(\*|\[\S+\](?:[\s\t]+\[\S+\])*)"
                +
                # recv [x=330,y=250]
                r"(?:[\s\t]+(recv|send)[\s\t]+(\*|\[\S+\](?:[\s\t]+\[\S+\])*))?"
            ),
            "names": ["pt", "dir1", "attrs1", "dir2", "attrs2"],
            "format": lambda o: "imageattr:%s %s %s"
            + (" %s %s" if o.get("dir2") != None else ""),
        },
        {
            # a=simulcast:send 1,2,3;~4,~5 recv 6;~7,~8
            # a=simulcast:recv 1;4,5 send 6;7
            "name": "simulcast",
            "reg": re.compile(
                # a=simulcast:
                r"^simulcast:"
                +
                # send 1,2,3;~4,~5
                r"(send|recv) ([a-zA-Z0-9\-_~;,]+)"
                +
                # space + recv 6;~7,~8
                r"(?:\s?(send|recv) ([a-zA-Z0-9\-_~;,]+))?"
                +
                # end
                r"$"
            ),
            "names": ["dir1", "list1", "dir2", "list2"],
            "format": lambda o: "simulcast:%s %s"
            + (" %s %s" if o.get("dir2") != None else ""),
        },
        {
            # old simulcast draft 03 (implemented by Firefox)
            #   https://tools.ietf.org/html/draft-ietf-mmusic-sdp-simulcast-03
            # a=simulcast: recv pt=97;98 send pt=97
            # a=simulcast: send rid=5;6;7 paused=6,7
            "name": "simulcast_03",
            "reg": r"^simulcast:[\s\t]+([\S+\s\t]+)$",
            "names": ["value"],
            "format": "simulcast: %s",
        },
        {
            # a=framerate:25
            # a=framerate:29.97
            "name": "framerate",
            "reg": r"^framerate:(\d+(?:$|\.\d+))",
            "format": "framerate:%s",
        },
        {
            # RFC4570
            # a=source-filter: incl IN IP4 239.5.2.31 10.1.15.5
            "name": "sourceFilter",
            "reg": r"^source-filter: *(excl|incl) (\S*) (IP4|IP6|\*) (\S*) (.*)",
            "names": [
                "filterMode",
                "netType",
                "addressTypes",
                "destAddress",
                "srcList",
            ],
            "format": "source-filter: %s %s %s %s %s",
        },
        {
            # a=bundle-only
            "name": "bundleOnly",
            "reg": r"^(bundle-only)",
        },
        {
            # a=label:1
            "name": "label",
            "reg": r"^label:(.+)",
            "format": "label:%s",
        },
        {
            # RFC version 26 for SCTP over DTLS
            # https://tools.ietf.org/html/draft-ietf-mmusic-sctp-sdp-26#section-5
            "name": "sctpPort",
            "reg": r"^sctp-port:(\d+)$",
            "format": "sctp-port:%s",
        },
        {
            # RFC version 26 for SCTP over DTLS
            # https://tools.ietf.org/html/draft-ietf-mmusic-sctp-sdp-26#section-6
            "name": "maxMessageSize",
            "reg": r"^max-message-size:(\d+)$",
            "format": "max-message-size:%s",
        },
        {
            # RFC7273
            # a=ts-refclk:ptp=IEEE1588-2008:39-A7-94-FF-FE-07-CB-D0:37
            "push": "tsRefClocks",
            "reg": r"^ts-refclk:([^\s=]*)(?:=(\S*))?",
            "names": ["clksrc", "clksrcExt"],
            "format": lambda o: "ts-refclk:%s"
            + ("=%s" if o.get("clksrcExt") != None else ""),
        },
        {
            # RFC7273
            # a=mediaclk:direct=963214424
            "name": "mediaClk",
            "reg": r"^mediaclk:(?:id=(\S*))? *([^\s=]*)(?:=(\S*))?(?: *rate=(\d+)\/(\d+))?",
            "names": [
                "id",
                "mediaClockName",
                "mediaClockValue",
                "rateNumerator",
                "rateDenominator",
            ],
            "format": lambda o: "mediaclk:"
            + ("id=%s %s" if o.get("id") != None else "%s")
            + ("=%s" if o.get("mediaClockValue") != None else "")
            + (" rate=%s" if o.get("rateNumerator") != None else "")
            + ("/%s" if o.get("rateDenominator") != None else ""),
        },
        {
            # a=keywds:keywords
            "name": "keywords",
            "reg": r"^keywds:(.+)$",
            "format": "keywds:%s",
        },
        {
            # a=content:main
            "name": "content",
            "reg": r"^content:(.+)",
            "format": "content:%s",
        },
        # BFCP https://tools.ietf.org/html/rfc4583
        {
            # a=floorctrl:c-s
            "name": "bfcpFloorCtrl",
            "reg": r"^floorctrl:(c-only|s-only|c-s)",
            "format": "floorctrl:%s",
        },
        {
            # a=confid:1
            "name": "bfcpConfId",
            "reg": r"^confid:(\d+)",
            "format": "confid:%s",
        },
        {
            # a=userid:1
            "name": "bfcpUserId",
            "reg": r"^userid:(\d+)",
            "format": "userid:%s",
        },
        {
            # a=floorid:1
            "name": "bfcpFloorId",
            "reg": r"^floorid:(.+) (?:m-stream|mstrm):(.+)",
            "names": ["id", "mStream"],
            "format": "floorid:%s mstrm:%s",
        },
        {
            # a=mid:1
            "name": "mid",
            "reg": r"^mid:([^\s]*)",
            "format": "mid:%s",
        },
        {
            # any a= that we don't understand is kept verbatim on media.invalid
            "push": "invalid",
            "names": ["value"],
        },
    ],
}


for key in grammar.keys():
    objs = grammar[key]
    for obj in objs:
        if not obj.get("reg"):
            obj["reg"] = r"(.*)"
        if not obj.get("format"):
            obj["format"] = "%s"
