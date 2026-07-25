# MadArtist VoiceChange 默认服务器 文档
该服务器是 MadArtist VoiceChange 项目中的默认服务器，用于处理变声请求，并返回变声后的音频文件。
## 端口占用情况
该服务器占用的端口是 5418
## API 文档
该服务器使用了 rpyc 库，提供了以下 API：
### Func vc_single__
变声主函数。
该函数的定义如下：
```python
def vc_single__(self,
                            input_audio0,
                            file_index,
                            spk_item : int = 0,
                            vc_transform0 : int = 0,
                            f0method0 : str = "rmvpe",
                            index_rate1 : float = 0.75,
                            filter_radius0 : int = 3,
                            resample_sr0 : int = 0,
                            rms_mix_rate0 : float = 0.25,
                            protect0 : float = 0.33,):
        ''':param spk_item: 说话人id
        :param input_audio0: 输入待处理音频文件路径
        :param vc_transform0: 变调(整数, 半音数量, 升八度12降八度-12)
        :param f0method0: 选择音高提取算法,输入歌声可用pm提速,harvest低音好但巨慢无比,crepe效果好但吃GPU,rmvpe效果最好且微吃GPU
        :param file_index: 特征检索库文件路径
        :param index_rate1: 检索特征占比
        :param filter_radius0: >=3则使用对harvest音高识别的结果使用中值滤波，数值为滤波半径，使用可以削弱哑音
        :param resample_sr0: 后处理重采样至最终采样率，0为不进行重采样
        :param rms_mix_rate0: 输入源音量包络替换输出音量包络融合比例，越靠近1越使用输出包络
        :param protect0: 保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果
        :return OutputName: 输出音频文件
        :return sample_rate: 输出音频采样率
        '''
```
#### 参数说明
- **input_audio0**: 输入待处理音频文件路径。
- **file_index**: 特征检索库文件路径。
- **spk_item**: 说话人id。
- **vc_transform0**: 变调(整数, 半音数量, 升八度12降八度-12)。
- **f0method0**: 选择音高提取算法,输入歌声可用pm提速,harvest低音好但巨慢无比,crepe效果好但吃GPU,rmvpe效果最好且微吃GPU。
- **index_rate1**: 检索特征占比。
- **filter_radius0**: >=3则使用对harvest音高识别的结果使用中值滤波，数值为滤波半径，使用可以削弱哑音。
- **resample_sr0**: 后处理重采样至最终采样率，0为不进行重采样。
- **rms_mix_rate0**: 输入源音量包络替换输出音量包络融合比例，越靠近1越使用输出包络。
- **protect0**: 保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果。
#### 返回值说明
- **OutputName**: 输出音频文件。
- **sample_rate**: 输出音频采样率。
#### 调用示例
```python
import rpyc
conn = rpyc.connect("localhost", 5418)

OutputName, sample_rate = conn.root.vc_single__(input_audio0="path/to/input/audio.wav", 
                                               file_index="path/to/index/file", 
                                               spk_item=0, 
                                               vc_transform0=0, 
                                               f0method0="rmvpe",
                                               index_rate1=0.75, 
                                               filter_radius0=3, 
                                               resample_sr0=0, 
                                               rms_mix_rate0=0.25, 
                                               protect0=0.33)
```
### Func get_vc
用于修改变声器输出人声。
该函数的定义如下：
```python
def get_vc(self,
                       sid0, 
                       protect : float = 0.33):
        ''':param sid0: 推理音色
        :param protect: 保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果
        :return spk_item: 说话人id
        :return protect: 保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果
        :return file_index: 自动检测index路径
        '''
```
#### 参数说明
- **sid0**: 推理音色。
- **protect**: 保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果。
#### 返回值说明
- **spk_item**: 说话人id。
- **protect**: 保护清辅音和呼吸声，防止电音撕裂等artifact，拉满0.5不开启，调低加大保护力度但可能降低索引效果。
- **file_index**: 自动检测index路径。
#### 调用示例
```python
import rpyc
conn = rpyc.connect("localhost", 5418)

spk_item, protect, file_index = conn.root.get_vc(sid0="path/to/sid", protect=0.33)
```