import os
import time
import json
from openai import OpenAI
import logging
from .config import (
    OPENAI_API_KEY,
    OPENAI_TIMEOUT,
    CHAT_MODEL,
    MAX_TEMPERATURE,
    MAX_TOKENS,
    CONVERSATION_STREAMING_PROMPT
)


class ConversationStreamingManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConversationStreamingManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.client = OpenAI(
            api_key=OPENAI_API_KEY, 
            timeout=OPENAI_TIMEOUT
        )
        self.model = CHAT_MODEL
        self.temperature = MAX_TEMPERATURE
        self.max_tokens = MAX_TOKENS
        self.prompt = CONVERSATION_STREAMING_PROMPT
    
    def generate_response(self, conversations_str):
        
        conversations = [{
            "role": "system", 
            "content": conversations_str
        }]

        conversations.append({
            "role": "system", 
            "content": CONVERSATION_STREAMING_PROMPT
        })

        # check conversation if it has 0,1 admin_action
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=conversations,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
       
        ai_response = response.choices[0].message.content   
        print(ai_response)
        return

        ai_response = json.loads(ai_response)
        return ai_response
    
    def store_knowledge_content(self, ai_response):
        
        print(ai_response)
        
        for item in ai_response:
          question = item.get("question", None)
          answer = item.get("answer", None)
          category = item.get("category", None)
          subcategory = item.get("subcategory", None)
          language = item.get("language", 2)










def main():
    # Example conversation data (replace with actual conversation data)
    conversations_str = """
    [
            {
              "ChatId": 10950634,
              "UserMsg": "boss bagi link download pusyy",
              "RobotMsg": "Hi boss, you want the 4D JOKER download link, right? 😊 \n\n📥 Here it is for you: [Download 4D JOKER](https://4djokers.club/chat/download/joker)\n\nHope you have a great time with it! Good luck! 🍀🚀🔥",
              "AdminReply": "",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:20:25",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 10950644,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "hntr semula resit tadi ke top-up , LAST CLAIM\r\nminta boss semak senarai akaun bank dlm apps dulu sebelum transfer ya\r\nTerima Kasih banyak2 bosss❤",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:21:01",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": true,
              "AdminAction": 3
            },
            {
              "ChatId": 10950651,
              "UserMsg": "ok",
              "RobotMsg": "Hehe good boss! 😆👍 Next time don’t forget to add the reference ya, it helps the system confirm faster. Hope you get big ONG and strong HUAT today! 🍀🔥💰",
              "AdminReply": "",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:21:15",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 10950655,
              "UserMsg": "bagi link  download pusyy boss",
              "RobotMsg": "Hi boss, if you want to download Kiss918, use these links below:\n\n📥 Kiss918 Download:\n🔗 [https://m-918kiss.com](https://m-918kiss.com)\n🔗 [http://b1.918kiss.com](http://b1.918kiss.com)\n\n📌 After downloading, log in using the ID & Password from the Joker App.\n📌 Make sure to transfer credit into the game before starting.\n\nIf there’s an issue with downloading or logging in, just let me know! 😊🙏",
              "AdminReply": "",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:21:25",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 10950671,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Link Mega\r\n\r\nhttps://m.cfbz888.com\r\nhttp://m.mega266.com\r\nhttps://m2.mega166.com\r\n\r\nLink Pussy888\r\n\r\nhttp://ytl.pussy888.com\r\n\r\nLink Kiss918\r\n\r\nhttps://m-918kiss.com\r\nhttp://b1.918kiss.com\r\n\r\nLINK XE\r\n\r\nhttps://m-xe88.com",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:22:22",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": true,
              "AdminAction": 3
            },
            {
              "ChatId": 10950701,
              "UserMsg": "tak boleh bukak boss",
              "RobotMsg": "Hi boss, if the game won’t open, let’s try a few steps to fix it:\n\n📌 How to fix the game not opening:\n1️⃣ Close & reopen the game app.\n2️⃣ Log out & log back into the Joker App, then try again.\n3️⃣ Switch your internet connection (try WiFi or mobile data).\n4️⃣ Check if the game is under maintenance – if so, just wait until it’s done.\n5️⃣ If all else fails, try reinstalling the game using the correct link.\n\nIf it still doesn’t work, send a screenshot of any error you see, and we’ll help you out! 😊🙏",
              "AdminReply": "",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:24:25",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 10950714,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "screenshot mari bos",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:25:35",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": true,
              "AdminAction": 3
            },
            {
              "ChatId": 10950718,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ReplyChatId": 0,
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250313/8a30948f-9037-46a9-9303-6c6b2f904397.jpg",
              "CreateDate": "2025-03-13 23:26:06",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 10950729,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, kalau login loading lama, boleh cuba cara ini:\r\n\r\n📌 Cara Atasi Login Loading Lama:\r\n✅ Tutup & buka semula app game.\r\n✅ Logout & login semula ke Joker App, kemudian salin semula ID & Password.\r\n✅ Tukar rangkaian internet (cuba WiFi atau data mobile).\r\n✅ Semak jika game tengah maintenance – kalau maintenance, tunggu sehingga selesai.\r\n✅ Cuba guna VPN jika masih tidak boleh buka:\r\n\r\n📥 Download VPN Malaysia:\r\n🔗 https://play.google.com/store/apps/details?id=malaysia.vpn_tap2free&hl=en&gl=US\r\n1️⃣ Pasang VPN & buka aplikasi.\r\n2️⃣ Tekan \"Connect to Malaysia\" dan tunggu sehingga berjaya disambungkan.\r\n3️⃣ Selepas connect, cuba login semula ke game.\r\n\r\n📌 Kalau masih ada masalah, boleh hantar screenshot ke live chat untuk semakan segera. 😊🙏",
              "ReplyChatId": 0,
              "ImgUrl": "",
              "CreateDate": "2025-03-13 23:26:57",
              "ConversationId": "JS5DwlUlpSSU/CIF5Tpakg==",
              "IsService": true,
              "AdminAction": 3
            }
          ]
"""

    manager = ConversationStreamingManager()
    ai_response = manager.generate_response(conversations_str)
    print(ai_response)
    
    # Output the AI response
    for item in ai_response:
      print(item)


if __name__ == "__main__":
    main()