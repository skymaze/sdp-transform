import os
import unittest

from sdp_transform import *


class TestMethods(unittest.TestCase):
    def test_parse_write(self):
        filenames = os.listdir('tests/sdps')
        for filename in filenames:
            if filename.endswith('sdp'):
                with open(f'tests/sdps/{filename}') as f:
                    sdp = f.read()
                    sdp_dict_1 = parse(sdp)
                    sdpStr = write(sdp_dict_1)
                    sdp_dict_2 = parse(sdpStr)
                    self.assertDictEqual(sdp_dict_1, sdp_dict_2)
    
    def test_parse_params_fmtp(self):
        with open('tests/sdps/normal.sdp') as f:
            sdp = f.read()
            sdp_dict = parse(sdp)
            video = sdp_dict['media'][1]
            vid_fmtp_1 = parseParams(video['fmtp'][0]['config'])
            self.assertEqual(vid_fmtp_1['profile-level-id'], '4d0028', 'video fmtp 0 profile-level-id')
            self.assertEqual(vid_fmtp_1['packetization-mode'], 1, 'video fmtp 0 packetization-mode')
            self.assertEqual(vid_fmtp_1['sprop-parameter-sets'], 'Z0IAH5WoFAFuQA==,aM48gA==', 'video fmtp 0 sprop-parameter-sets')
            vid_fmtp_2 = parseParams(video['fmtp'][1]['config'])
            self.assertEqual(vid_fmtp_2['minptime'], 10, 'video fmtp 1 minptime')
            self.assertEqual(vid_fmtp_2['useinbandfec'], 1, 'video fmtp 1 useinbandfec')

    def test_parse_params_rids(self):
        with open('tests/sdps/simulcast.sdp') as f:
            sdp = f.read()
            sdp_dict = parse(sdp)
            video = sdp_dict['media'][1]
            rid_1_params = parseParams(video['rids'][0]['params'])
            self.assertDictEqual(rid_1_params, {
                'pt': 97,
                'max-width': 1280,
                'max-height': 720,
                'max-fps': 30
            }, 'video 1st rid params')
            rid_2_params = parseParams(video['rids'][1]['params'])
            self.assertDictEqual(rid_2_params, {
                'pt': 98
            }, 'video 2nd rid params')
    
    def test_parse_image_attributes(self):
        with open('tests/sdps/simulcast.sdp') as f:
            sdp = f.read()
            sdp_dict = parse(sdp)
            video = sdp_dict['media'][1]
            image_attr_1_recv_params = parseImageAttributes(video['imageattrs'][0]['attrs2'])
            self.assertListEqual(image_attr_1_recv_params, [
                {'x': 1280, 'y': 720},
                {'x': 320, 'y': 180},
                {'x': 160, 'y': 90},
            ], 'video 1st imageattr recv params')
        
    def test_parse_simulcast_tream_list(self):
         with open('tests/sdps/simulcast.sdp') as f:
            sdp = f.read()
            sdp_dict = parse(sdp)
            video = sdp_dict['media'][1]
            simulcast_send_streams = parseSimulcastStreamList(video['simulcast']['list1'])
            self.assertListEqual(simulcast_send_streams, [
                [ {'scid': 1, 'paused': False}, {'scid': 4, 'paused': True} ],
                [ {'scid': 2, 'paused': False} ],
                [ {'scid': 3, 'paused': False} ]
            ])
            simulcast_recv_streams = parseSimulcastStreamList(video['simulcast']['list2'])
            self.assertListEqual(simulcast_recv_streams, [
                [ {'scid': 'c', 'paused': False} ]
            ], 'video simulcast recv streams')

if __name__ == '__main__':
    unittest.main()