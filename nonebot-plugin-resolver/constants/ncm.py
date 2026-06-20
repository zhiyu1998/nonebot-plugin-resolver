"""
NCM获取歌曲信息链接
"""
NETEASE_API_CN = 'https://www.markingchen.ink'

"""
NCM主解析接口
参数：id={歌曲ID}
示例：http://itapi.top/API/get_wyyid.php?id=123456
返回字段：code / message / data[0].name / picurl / singers / url
"""
NETEASE_TEMP_API = "http://itapi.top/API/get_wyyid.php?id={}"

"""
NCM备用解析接口
参数：type=json&ids={歌曲ID}&level=hires
返回字段通常为：url / pic / ar_name / name
"""
NETEASE_TEMP_API_FALLBACK = "https://api.bugpk.com/api/163_music?type=json&ids={}&level=hires"
