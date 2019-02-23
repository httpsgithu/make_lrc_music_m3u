# -*- encoding:utf-8 -*-

# 网易云音乐 lrc歌曲m3u生成器
# 版本: 6.0
import platform
import sys
import codecs
import hashlib
import json
import os
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
from sys import argv


if len(argv) < 2:
    print("请传入歌单id")
    sys.exit()

# 歌单id设置 设置为 argv[1] 将使用 " python make_lrc_music_m3u.py 歌单id " 这种方式传入
playlistId = argv[1]

# 播放列表存放位置
m3udir = "./播放列表/"

# 相对于播放列表存放位置的 音乐存放位置
mp3dir_in_m3udir = "../音乐/"

# 是否按m3u分类
if len(argv) > 2:
    sortBym3u = True
else:
    sortBym3u = False

# 是否下载歌词
downLrc = True

# 加载头部 防ban
opener = urllib.request.build_opener()
opener.addheaders = [
    ('Accept','*/*'),
    ('Accept-Language','zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4'),
    ('Connection','keep-alive'),
    ('Content-Type','application/x-www-form-urlencoded'),
    ('Referer','http://music.163.com'),
    ('Host','music.163.com'),
    ('User-Agent','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36')
]
urllib.request.install_opener(opener)

# 判断文件是否存在
def hasFile(fileName):
    if fileName in listdir:
        return True
    else:
        return False


# 半角转全角
def half2full(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:
            inside_code += 65248

        rstring += chr(inside_code)
    return rstring


# 发送请求
def urlGetJsonLoad(url):
    try:
        return json.load(urllib.request.urlopen(url))
    except:
        print('error')


# 替换文件名不允许字符
def replaceName(name):
    name = name.replace('?', half2full('?'))
    name = name.replace('*', half2full('*'))
    name = name.replace('/', half2full('/'))
    name = name.replace('\\', half2full('\\'))
    name = name.replace('<', half2full('<'))
    name = name.replace('>', half2full('>'))
    name = name.replace(':', half2full(':'))
    name = name.replace('\"', half2full('\"'))
    name = name.replace('|', half2full('|'))
    name = name.replace('[', half2full('['))
    name = name.replace(']', half2full(']'))
    name = name.strip()
    return name


# 获取歌词
def getLrc(tracksId):
    url = 'http://music.163.com/api/song/lyric?lv=-1&tv=-1&id=' + tracksId
    dataS = urlGetJsonLoad(url)
    if dataS['code'] != 200:
        ecode = str(dataS['code'])
        print('errorCode: ' + ecode)
    else:
        if 'lrc' not in dataS or 'lyric' not in dataS['lrc'] or dataS['lrc']['lyric'] == None:
            return ''

        if 'tlyric' not in dataS or 'lyric' not in dataS['tlyric'] or dataS['tlyric']['lyric'] == None:
            return dataS['lrc']['lyric']

        # 按换行分割
        lrcL = dataS['lrc']['lyric'].splitlines()
        tlyricL = dataS['tlyric']['lyric'].splitlines()
        tlyricD = {}
        lrcStr = ''

        # 分割翻译
        for tlyric in tlyricL:
            tl = tlyric.split(']', 1)
            # 防止有时间但翻译为空
            if len(tl) > 1:
                tlyricD[tl[0]] = tl[1]

        # 合并歌词
        for lrc in lrcL:
            l = lrc.split(']', 1)
            if l[0] in tlyricD:
                lrcStr += l[0] + ']' + l[1] + '\t' + tlyricD[l[0]] + '\n'
            else:
                lrcStr += lrc + '\n'

        return lrcStr


# 下载歌曲
def dowmMusic(tracksId, fileName):
    url = 'http://music.163.com/song/media/outer/url?id=' + tracksId + '.mp3'
    try:
        print('Download music: ' + fileName.replace(m3udir, '').replace(mp3dir, ''))
    except:
        print('Download music: ' + tracksId)
    try:
        urllib.request.urlretrieve(url, fileName)
    except:
       print('error')


# 写出文件
def writeToFile(name, text):
    try:
        print('Write to file: ' + name.replace(m3udir, '').replace(mp3dir, ''))
    except:
        print('Write to file: ')
    try:
        file = codecs.open(name, "w", "utf-8")
        file.write(text)
        file.close()
    except:
        print('error')


# 生成播放列表
m3uText = "#EXTM3U"


def addPlaylist(mp3Title, mp3Name):
    global m3uText
    m3uText += "\n#EXTINF:" + mp3Title + "\n" + mp3dir.replace("/", "\\") + mp3Name


# 确保需要的文件夹
if not os.path.isdir(m3udir):
    os.mkdir(m3udir)

if not os.path.isdir(m3udir + mp3dir_in_m3udir):
    os.mkdir(m3udir + mp3dir_in_m3udir)

# 获取歌单
url = 'http://music.163.com/api/playlist/detail?id=' + playlistId
dataL = urlGetJsonLoad(url)
if dataL['code'] != 200:
    ecode = str(dataL['code'])
    print('errorCode: ' + ecode)
else:
    m3uName = replaceName(dataL['result']['name'])
    allNum = len(dataL['result']['tracks'])
    nowNum = 0

    # 如按歌单分文件夹,不存在文件夹就创建
    if sortBym3u:
        mp3dir = mp3dir_in_m3udir + m3uName + "/"
        if not os.path.isdir(m3udir + mp3dir):
            os.mkdir(m3udir + mp3dir)

    else:
        mp3dir = mp3dir_in_m3udir

    # 查找所有文件
    listdir = os.listdir(m3udir + mp3dir)

    # 循环歌单
    for tracks in dataL['result']['tracks']:
        nowNum += 1
        print("\r" + str(nowNum) + '/ ' + str(allNum), end=' ')
        fileName = ''
        fileNameAndroid = ''
        fileNameReverse = ''
        # 循环歌手
        i = len(tracks['artists']) - 1
        for artist in tracks['artists']:
            if i > 0:
                fileName += artist['name'] + ","
                fileNameAndroid += artist['name'] + " "
                fileNameReverse = "," + artist['name'] + fileNameReverse
                i -= 1
            else:
                fileName += artist['name']
                fileNameAndroid += artist['name']
                fileNameReverse = artist['name'] + fileNameReverse


        fileName += " - " + tracks['name']
        fileName = replaceName(fileName)
        
        tid = str(tracks['id'])
        # 存在歌曲文件跳过
        if not hasFile(fileName + ".mp3"):
            # 如果是按照空格分隔歌手,例如Android端
            fileNameAndroid += " - " + tracks['name'].strip()
            fileNameAndroid = replaceName(fileNameAndroid.replace('/',' ').replace('*',' ').replace('+', half2full('+')).replace('\"','”'))
            if fileNameAndroid != fileName and hasFile(fileNameAndroid + ".mp3"):
                try:
                    print('Rename file: ' + fileNameAndroid + ".mp3")
                except:
                    print('Rename file: ')
                    
                os.rename(m3udir + mp3dir + fileNameAndroid + ".mp3", m3udir + mp3dir + fileName + ".mp3")
            else:
                # 最近网易整理了一下歌手,处理一下已有文件翻转的情况
                fileNameReverse += " - " + tracks['name'].strip()
                fileNameReverse = replaceName(fileNameReverse)
                if fileNameAndroid != fileName and fileNameReverse != fileName and fileNameAndroid != fileNameReverse and hasFile(fileNameReverse + ".mp3"):
                    try:
                        print('Rename file: ' + fileNameReverse + ".mp3")
                    except:
                        print('Rename file: ')

                    os.rename(m3udir + mp3dir + fileNameReverse + ".mp3", m3udir + mp3dir + fileName + ".mp3")
                else:
                    # 这里将下载一个无信息的128kbps的版本
                    dowmMusic(tid, m3udir + mp3dir + fileName + ".mp3")

        # 如果需要下载歌词,不存在歌词就下载
        if downLrc:
            if not hasFile(fileName + ".lrc"):
                lrcS = getLrc(tid)
                if len(lrcS) > 0:
                    writeToFile(m3udir + mp3dir + fileName + ".lrc", lrcS)

        # 添加到播放列表
        addPlaylist(tracks['name'], fileName + ".mp3")

    # 写播放列表文件
    writeToFile(m3udir + m3uName + ".m3u", m3uText)
    