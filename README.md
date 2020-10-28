# sdp-transform

A simple Python parser and writer of SDP. Defines internal grammar based on [RFC4566 - SDP](http://tools.ietf.org/html/rfc4566), [RFC5245 - ICE](http://tools.ietf.org/html/rfc5245), and many more.

## Reference
[JavaScript Version sdp-transform](https://github.com/clux/sdp-transform)

## Installing
```
pip install sdp-transform
```


## Usage
```python
import sdp_transform

# parse str to dict
sdp_dict = sdp_transform.parse("v=0\r\no=- 20518 0 IN IP4 203.0.113.1\r\ns= \r\nt=0 0\r\nc=IN IP4 203.0.113.1\r\na=ice-ufrag:F7gI\r\na=ice-pwd:x9cml/YzichV2+XlhiMu8g\r\na=fingerprint:sha-1 42:89:c5:c6:55:9d:6e:c8:e8:83:55:2a:39:f9:b6:eb:e9:a3:a9:e7\r\nm=audio 54400 RTP/SAVPF 0 96\r\na=rtpmap:0 PCMU/8000\r\na=rtpmap:96 opus/48000\r\na=ptime:20\r\na=sendrecv\r\na=candidate:0 1 UDP 2113667327 203.0.113.1 54400 typ host\r\na=candidate:1 2 UDP 2113667326 203.0.113.1 54401 typ host\r\nm=video 55400 RTP/SAVPF 97 98\r\na=rtpmap:97 H264/90000\r\na=fmtp:97 profile-level-id=4d0028;packetization-mode=1\r\na=rtpmap:98 VP8/90000\r\na=sendrecv\r\na=candidate:0 1 UDP 2113667327 203.0.113.1 55400 typ host\r\na=candidate:1 2 UDP 2113667326 203.0.113.1 55401 typ host\r\n")

# write dict to str
sdp_str = sdp_transform.write(sdp_dict)
```