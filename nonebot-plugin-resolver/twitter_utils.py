import tweepy

# 扩展代理
class TweepyWithProxy(tweepy.Client):
    def __init__(self, proxies, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session.proxies = proxies