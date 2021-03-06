import random
import time
from flask import Flask, request, abort
from imgurpython import ImgurClient

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import tempfile, os
from config import client_id, client_secret, album_id, album_id_lucky, access_token, refresh_token, line_channel_access_token, \
    line_channel_secret

import json

app = Flask(__name__)

line_bot_api = LineBotApi(line_channel_access_token)
handler = WebhookHandler(line_channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'


@handler.add(MessageEvent, message=(ImageMessage, TextMessage, VideoMessage, AudioMessage))
def handle_message(event):
    if isinstance(event.message, ImageMessage):
        msgSource = line_bot_api.get_profile(event.source.user_id)
        userDisplayName = msgSource.display_name
        ext = 'jpg'
        message_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
        dist_path = tempfile_path + '.' + ext
        dist_name = os.path.basename(dist_path)
        os.rename(tempfile_path, dist_path)
        try:
            client = ImgurClient(client_id, client_secret, access_token, refresh_token)
            config = {
                'album': album_id,
                'name': userDisplayName,
                'title': userDisplayName,
                'description': userDisplayName + ' uploaded'
            }
            path = os.path.join('static', 'tmp', dist_name)
            client.upload_from_path(path, config=config, anon=False)
            os.remove(path)
            print(path)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='您的照片上傳成功，請保留相片至婚禮結束，謝謝您!'))
        except:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='您的照片上傳失敗，請重新試試!'))
        return 0

    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='您上傳的影片無法投影在相片牆'))
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='您上傳的聲音訊息無法投影在相片牆'))
    elif isinstance(event.message, TextMessage):
        if event.message.text == "啾咪神之手":
            imageSize = "h"
            client = ImgurClient(client_id, client_secret)
            images = client.get_album_images(album_id_lucky)
            index = [0,0]
            imgurNameA = "A"
            imgurNameB = "A"
            while imgurNameA == imgurNameB:
                index = [random.randint(0, len(images) - 1) for _ in range(2)]
                imgurNameA = images[index[0]].title
                imgurNameB = images[index[1]].title
                print(index, imgurNameA, imgurNameB)
                imgurNameList = [imgurNameA, imgurNameB]
                imgurNameListIndex = 0
                image_message_list = []
            for i in index:
                imgurLink = images[i].link
                linkIndex = imgurLink.find('.jpg')
                trgUrl = imgurLink[:linkIndex] + imageSize + imgurLink[linkIndex:]
                # image_message_list.append(ImageSendMessage(
                #     original_content_url=trgUrl,
                #     preview_image_url=trgUrl
                # ))
                image_message_list.append(FlexSendMessage(
                    alt_text = 'hello',
                    contents = {
                        "type": "bubble",
                        "hero": {
                            "type": "image",
                            "url": trgUrl,
                            "size": "full",
                            "aspectRatio": "30:30",
                            "aspectMode": "cover"
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                "type": "text",
                                "text": imgurNameList[imgurNameListIndex],
                                "size": "3xl",
                                "weight": "bold",
                                "color": "#0000E3"
                                },
                                {
                                "type": "text",
                                "text": '恭喜幸運中獎!!!',
                                "size": "xl",
                                "weight": "bold",
                                "color": "#FF0000"
                                }
                            ]
                        }
                    }
                ))
                imgurNameListIndex += 1
            print(image_message_list)
            # line_bot_api.reply_message(
            #     event.reply_token, [
            #         image_message_list[0],
            #         TextSendMessage(text='恭喜{'+ imgurNameA + '}幸運中獎!!!'),
            #         image_message_list[1],
            #         TextSendMessage(text='恭喜{'+ imgurNameB + '}幸運中獎!!!'),
            #     ])
            line_bot_api.reply_message(
                event.reply_token, [
                    image_message_list[0],
                    image_message_list[1],
                ])

            return 0

        #測試msg
        # elif event.message.text == '婚禮資訊':
        #     with open('./asset/weddingInfo.json','r') as winfo:
        #         weddingInfo = json.load(winfo)
        #         print(weddingInfo)
        #     flex_message = FlexSendMessage(
        #             alt_text='婚禮資訊',
        #             contents = weddingInfo
        #         )
        #     print(flex_message)
        #     line_bot_api.reply_message(
        #         event.reply_token, [
        #             flex_message,
        #             TextSendMessage(text=' yoyo'),
        #             TextSendMessage(text='請傳一張圖片給我')
        #         ])
        #測試msg
        else:
            # line_bot_api.reply_message(
            #     event.reply_token, [
            #         TextSendMessage(text=' yoyo'),
            #         TextSendMessage(text='請傳一張圖片給我')
            #     ])
            return 0

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event)
    if(event.postback.data=='action=weddingInfo'):
        with open('./asset/weddingInfo.json','r') as winfo:
            weddingInfo = json.load(winfo)
        flex_message = FlexSendMessage(
                alt_text = '婚禮資訊',
                contents = weddingInfo
            )
        line_bot_api.reply_message(
            event.reply_token, [
                    flex_message
                ])
        return 0
    elif(event.postback.data=='action=trafficInfo'):
        with open('./asset/trafficInfo.json','r') as trffo:
            trafficInfo = json.load(trffo)
        flex_message = FlexSendMessage(
                alt_text = '交通資訊',
                contents = trafficInfo
            )
        line_bot_api.reply_message(
            event.reply_token, [
                    flex_message
                ])
        return 0

if __name__ == '__main__':
    app.run()
