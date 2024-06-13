# -*- coding: utf-8 -*-
from PIL import Image, ImageFont, ImageDraw
import time, sys


def createShareImg(content):
    template_img = Image.open(r'resources\template.jpg')  # 600*1000
    avatar_img = Image.open(r'resources\avatar.jpg')  # 248*220
    qrcode_img = Image.open(r'resources\qrcode.jpg')  # 280*280

    # 将背景图片和圆形头像合成之后当成新的背景图片
    template_img = drawCircleAvatar(avatar_img, template_img)

    # 将二维码图片粘贴在背景图片上
    region = qrcode_img
    region = region.resize((180, 180))
    template_img.paste(region, (int((600 - 180) / 2), 800))

    # 绘制用户昵称
    font1 = ImageFont.truetype("msyh.ttc", 30)
    drawImage = ImageDraw.Draw(template_img)
    (content_width, content_height) = drawImage.textsize(content, font1)
    drawImage.text((int((600 - content_width) / 2), 300), content, font=font1)

    # 保存图片到文件
    template_img.save('output.jpg')  # 保存图片


# 将头像变成圆形绘制在背景图片上，然后将合成的图片对象返回
def drawCircleAvatar(im, background):
    im = im.resize((150, 150));
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    # 遮罩对象
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    # 画椭圆的方法
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    im.putalpha(mask)
    background.paste(im, (int((600 - 150) / 2), 100), im)
    return background


if __name__ == '__main__':
    content = '''急涨急跌
交易所：ftx
币种：dmg/usd
现价：$0.019128
今日涨幅：9.97%
1分钟涨幅：-3.87%
3分钟交易额：$0.78万
3分钟净流入：$-0.46万
3分钟交易/大单数：73/0
3分钟买/卖单数：16/57
今日交易/大单数：321/0
今日买/卖单数：154/167
时间：2022-10-21 16:23:29'''

    createShareImg(content)
