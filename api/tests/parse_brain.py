from openai import OpenAI

# Configure sua API key
api_key =""
# Exemplo de prompt
prompt = """
Abaixo, você tem uma conversa de atendimento:

  {
      "MemberId": 161111,
      "ConversationsList": [
        {
          "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
          "Conversations": [
            {
              "ChatId": 11361327,
              "UserMsg": "Hi ",
              "RobotMsg": "Saya faham, boss! Jika ada apa-apa yang anda perlukan atau soalan lain, jangan ragu untuk bertanya. Semoga berjaya dalam permainan anda! 🍀🔥💰",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:55:11",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11361332,
              "UserMsg": "Pagang vs kedah foodball bet how much ",
              "RobotMsg": "Saya faham, boss! Untuk pertaruhan antara Pagang dan Kedah, jumlah pertaruhan bergantung kepada jenis pertaruhan yang anda buat. Jika anda bercakap tentang pertaruhan khas, pastikan anda semak slip anda untuk memastikan semuanya betul. Jika ada masalah dengan pembayaran, hantar tangkapan skrin kepada kami, dan kami akan bantu selesaikan! 😊⚽️",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:55:42",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11361335,
              "UserMsg": "Pahang ",
              "RobotMsg": "Saya faham, boss! Jika anda bercakap tentang pertaruhan Pahang, jumlah pertaruhan bergantung kepada pilihan anda. Pastikan anda semak semua maklumat sebelum membuat pertaruhan. Jika ada masalah atau pertanyaan lain, beritahu saya ya! 😊⚽️",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:55:51",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11361342,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, kemenangan bet bola akan masuk ke wallet secara automatik dalam masa 24 jam pada hari yang sama. ⚽💰\r\n\r\n📌 Mohon bersabar ya boss, sistem sedang proses. Kalau masih belum masuk selepas 24 jam, boleh roger kami di live chat untuk semakan.\r\n\r\nTerima kasih atas kesabaran boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:56:20",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11361343,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, kemenangan bet bola akan masuk ke wallet secara automatik dalam masa 24 jam pada hari yang sama. ⚽💰\r\n\r\n📌 Mohon bersabar ya boss, sistem sedang proses. Kalau masih belum masuk selepas 24 jam, boleh roger kami di live chat untuk semakan.\r\n\r\nTerima kasih atas kesabaran boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:56:21",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11361366,
              "UserMsg": "No want see score bet how much ",
              "RobotMsg": "Saya faham, boss! Jika anda hanya menerima RM8 untuk pertaruhan khas yang sepatutnya membayar RM210, mungkin ada kesilapan pada slip pertaruhan anda. Pastikan format pertaruhan itu betul. Jika semuanya nampak baik, hantar tangkapan skrin kepada kami, dan saya akan bantu selesaikan masalah ini! 😊💰",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:58:55",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11361378,
              "UserMsg": "Time out redy ",
              "RobotMsg": "Saya faham, boss! Jika anda baru sahaja top-up tetapi masa pertaruhan sudah tamat, anda boleh menggunakan kredit itu untuk cabutan seterusnya atau cuba permainan lain seperti slot dan kasino langsung. 🎰🔥\n\n📌 Untuk cabutan 4D seterusnya, anda boleh bertaruh selepas jam 10 malam untuk cabutan yang akan datang.\n📌 Untuk mengelakkan terlepas nombor yang anda inginkan, adalah lebih baik untuk top-up lebih awal supaya anda boleh bertaruh sebelum tarikh akhir.\n\nJika ada soalan lain, balas kepada kami dalam live chat ya, boss! 😊🙏",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:00:06",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11361383,
              "UserMsg": "Ok ",
              "RobotMsg": "Baik, boss! Jika ada apa-apa lagi yang anda perlukan atau soalan lain, jangan ragu untuk bertanya. Saya sedia membantu! 😊👍",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:00:31",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11361393,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss 😊\r\n\r\nIf you want to check the score and your bet details:\r\n\r\n1️⃣ Tap the football icon (⚽) in the app\r\n2️⃣ Select the match you bet on\r\n3️⃣ Tap to view the results and bet details\r\n\r\nIf you still can’t find it, let me know which match and I’ll help you check ya boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:01:22",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11361396,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:01:25",
              "ConversationId": "h5SQyVYnV2pm/sgqwwepbA==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 161424,
      "ConversationsList": [
        {
          "ConversationId": "4NExfygX/6/DvrKMBpcXMQ==",
          "Conversations": [
            {
              "ChatId": 11345415,
              "UserMsg": "boss saya sudah transfer 80 orang punya ",
              "RobotMsg": "Terima kasih kerana berkongsi, boss! Anda memang rajin bekerja keras. Jika ada sebarang pertanyaan atau bantuan yang diperlukan, jangan ragu untuk berhubung dengan kami di live chat ya, boss! 😊👍",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 17:56:26",
              "ConversationId": "4NExfygX/6/DvrKMBpcXMQ==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11345418,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, kalau dah topup, pastikan resit sudah diupload ke halaman topup dalam app ya. 😊\r\n\r\n📌 Lepas upload, tunggu 1-10 minit untuk sistem sahkan transaksi.\r\n📌 Kalau lebih 10 minit masih belum masuk, boleh hantar resit transaksi ke live chat untuk semakan segera.\r\n\r\nTerima kasih atas kesabaran boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 17:56:49",
              "ConversationId": "4NExfygX/6/DvrKMBpcXMQ==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11345419,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 17:56:51",
              "ConversationId": "4NExfygX/6/DvrKMBpcXMQ==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        },
        {
          "ConversationId": "GtJOonkeKLkql7rIGeQHGg==",
          "Conversations": [
            {
              "ChatId": 11356859,
              "UserMsg": "bos saya sudah transfer 100 ",
              "RobotMsg": "Baik, boss! Jika anda sudah membuat pemindahan, sila muat naik resit lengkap ke halaman top-up dalam aplikasi, bukan di dalam chat langsung ya. 😊\n\n📌 Pastikan resit tersebut termasuk:\n✅ Tarikh & masa transaksi\n✅ Jumlah yang dipindahkan\n✅ Butiran penerima (akaun syarikat kami)\n✅ Status transaksi yang berjaya\n\nSelepas memuat naik, tunggu 3-10 minit untuk sistem mengesahkan. Jika ada masalah, balas kepada kami dalam chat langsung untuk pemeriksaan lanjut. 🙏🔥",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:47:42",
              "ConversationId": "GtJOonkeKLkql7rIGeQHGg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356862,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "sila uplaod slip bankin anda melalui (WALLET -> TOPUP ) proses ambil masa dalam 3-5min ,tq boss, mantap❤️❤️",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:47:56",
              "ConversationId": "GtJOonkeKLkql7rIGeQHGg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11356869,
              "UserMsg": "👌",
              "RobotMsg": "Sama-sama, boss! 🍀🔥💰 Jika ada apa-apa lagi yang anda perlukan, jangan ragu untuk bertanya ya! 😊",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:48:23",
              "ConversationId": "GtJOonkeKLkql7rIGeQHGg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356874,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Sama-sama, boss! 🍀🔥💰 Jika ada apa-apa lagi yang anda perlukan, jangan ragu untuk bertanya ya! 😊",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:48:43",
              "ConversationId": "GtJOonkeKLkql7rIGeQHGg==",
              "IsService": true,
              "AdminAction": 2
            }
          ]
        }
      ]
    },
    {
      "MemberId": 161804,
      "ConversationsList": [
        {
          "ConversationId": "skQhaglTasKfeAlzXWBBzw==",
          "Conversations": [
            {
              "ChatId": 11357611,
              "UserMsg": "sorry boss... salah",
              "RobotMsg": "Tak apa, boss! Semua orang buat silap. Ada yang boleh saya bantu?",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 18:29:08",
              "ConversationId": "skQhaglTasKfeAlzXWBBzw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11357637,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "hi boss ,ade ape yang saya boleh bantu ??☺️",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 18:29:54",
              "ConversationId": "skQhaglTasKfeAlzXWBBzw==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11357701,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "salah ",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 18:32:03",
              "ConversationId": "skQhaglTasKfeAlzXWBBzw==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 163427,
      "ConversationsList": [
        {
          "ConversationId": "cjSmH9pyk55VXmw1UVyfEw==",
          "Conversations": [
            {
              "ChatId": 11361795,
              "UserMsg": "boss tolong share link app joker boleh x member nak join",
              "RobotMsg": "Baik, boss! Jika anda ingin memuat turun 4D JOKER, gunakan pautan ini:\n\n📥 [Muat Turun 4D JOKER](https://4djokers.club/chat/download/joker)\n\n📌 Selepas memuat turun, pasang seperti biasa dan log masuk ke akaun anda. \n📌 Jika anda ingin mengesyorkan kepada rakan, pergi ke \"Profil\" dalam aplikasi dan salin \"Pautan Rujukan\" untuk pendaftaran.\n\nJika ada sebarang masalah semasa pemasangan, balas kepada kami dalam chat langsung untuk bantuan! 😊🙏\n\nSemoga anda mendapat banyak tuah dan HUAT besar, boss! 🍀🚀🔥",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:37:06",
              "ConversationId": "cjSmH9pyk55VXmw1UVyfEw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11361804,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, kalau kawan boss nak register, boleh ikut langkah ini:\r\n\r\n📌 Cara Daftar:\r\n1️⃣ Pergi ke \"Profile\" dalam app.\r\n2️⃣ Salin \"Referral Link\" yang ada dalam profile boss.\r\n3️⃣ Hantar link tersebut kepada kawan untuk daftar.\r\n4️⃣ Kawan boss boleh guna link tersebut untuk register & mula bermain.\r\n\r\n📌 Referral Link hanya boleh didapati dalam akaun boss sendiri dalam app.\r\n\r\nKalau ada masalah atau perlukan bantuan, boleh roger kami di live chat ya boss! 😊🙏",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:37:46",
              "ConversationId": "cjSmH9pyk55VXmw1UVyfEw==",
              "IsService": true,
              "AdminAction": 1
            },
            {
              "ChatId": 11361805,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/operator/20250408/59fe7970-099c-41af-9f00-d49e3bbe877d.png",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:37:51",
              "ConversationId": "cjSmH9pyk55VXmw1UVyfEw==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11361807,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 23:37:54",
              "ConversationId": "cjSmH9pyk55VXmw1UVyfEw==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 164962,
      "ConversationsList": [
        {
          "ConversationId": "SteytgLVeKTmvNLqqiYExg==",
          "Conversations": [
            {
              "ChatId": 11348899,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250407/4129c7cc-763f-4147-bd80-3ed8d1acf96d.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:43:40",
              "ConversationId": "SteytgLVeKTmvNLqqiYExg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11348902,
              "UserMsg": "nak claim macam mane boss",
              "RobotMsg": "Untuk membuat tuntutan, anda perlu memuat naik resit pembelian anda di sini, boss. Pastikan resit yang dimuat naik jelas dan lengkap untuk memudahkan proses tuntutan anda. Jika ada sebarang pertanyaan, jangan ragu untuk bertanya ya! 😉",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:43:51",
              "ConversationId": "SteytgLVeKTmvNLqqiYExg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11348907,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, kalau menang hadiah dari Lucky Spin, kredit akan masuk ke wallet secara automatik dalam masa 24 jam ya. 😊🎰\r\n\r\n📌 Duit Lucky Spin hanya boleh digunakan sebagai kredit betting.\r\n✅ 4D Betting\r\n✅ Football Betting\r\n✅ Slot Game (Mega888, Kiss918, XE88, Pussy888)\r\n✅ Live Casino\r\n📌 Tetapi kredit ini tidak boleh withdraw terus, perlu digunakan untuk bermain dahulu. Jika menang, barulah boleh withdraw ikut syarat turnover. 😊🔥\r\n📌 Boss boleh semak dalam wallet selepas 24 jam.\r\n\r\nKalau masih belum masuk selepas tempoh itu, boleh roger kami di live chat untuk semakan lanjut. 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:44:16",
              "ConversationId": "SteytgLVeKTmvNLqqiYExg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11348908,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:44:18",
              "ConversationId": "SteytgLVeKTmvNLqqiYExg==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        },
        {
          "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
          "Conversations": [
            {
              "ChatId": 11356263,
              "UserMsg": "boss",
              "RobotMsg": "Baik, boss! Ada yang boleh saya bantu?",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:03:25",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356265,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Baik, boss! Ada yang boleh saya bantu?",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:03:36",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": true,
              "AdminAction": 2
            },
            {
              "ChatId": 11356267,
              "UserMsg": "kenapa results hari ii xde?",
              "RobotMsg": "Hi boss, kalau keputusan belum dikemas kini, jangan risau, keputusan dan hadiah tetap akan dikeluarkan kepada pemenang. 😊\n\n📌 Waktu anggaran untuk pengumuman keputusan:\n🔹 J2 3PM & J3 3PM → 3:30PM - 4:00PM\n🔹 J2 9PM & J3 9PM → 9:30PM - 10:00PM\n🔹 Perdana 3PM & Lucky 3PM → 4:00PM - 4:30PM\n🔹 Perdana 7PM & Lucky 7PM → 8:00PM - 8:30PM\n\nKadang-kadang keputusan mungkin sedikit lewat, tetapi semua hadiah akan tetap dikreditkan seperti biasa. Terima kasih atas kesabaran anda, boss! 🙏🔥",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:03:42",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356270,
              "UserMsg": "tengok di Google hari ii ada 5114",
              "RobotMsg": "Faham, boss! Kalau ada 5114, mungkin ada masalah teknikal yang menyebabkan keputusan belum masuk. \n\nCuba semak semula sambungan internet atau log keluar dan masuk semula ke dalam akaun. Jika masih ada masalah, boleh hubungi kami melalui live chat untuk bantuan lanjut. Jangan risau, kita akan selesaikan secepat mungkin! 😊",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:03:58",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356275,
              "UserMsg": "lucky hari hari",
              "RobotMsg": "Saya faham perasaan boss. Kadang-kadang, nasib memang tidak menyebelahi kita. Tapi jangan risau, kerana keberuntungan boleh datang bila-bila masa! \n\nTeruskan bermain dengan tenang dan nikmati permainan. Semoga anda dapat kemenangan besar dalam pusingan seterusnya! 🍀🔥 Jika ada apa-apa yang boleh saya bantu, beritahu saja!",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:04:18",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356277,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "sabar2 ya bos semak balik nanti ya",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:04:36",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11356282,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "ChatGPT said:\r\nHi boss 😊\r\n\r\nSabar ya, sistem sekarang sedang dalam proses dan mungkin sedikit lambat hari ini. Mohon tunggu sebentar, dan keputusan akan muncul secepat mungkin. Terima kasih atas kesabaran boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:05:22",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11356285,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss 😊\r\n\r\nSabar ya, sistem sekarang sedang dalam proses dan mungkin sedikit lambat hari ini. Mohon tunggu sebentar, dan keputusan akan muncul secepat mungkin. Terima kasih atas kesabaran boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:05:27",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11356318,
              "UserMsg": "ok",
              "RobotMsg": "Baik, boss! Jika ada apa-apa lagi yang ingin ditanya atau dibincangkan, jangan segan-segan untuk beritahu saya. Saya sedia membantu! 😊",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 17:08:54",
              "ConversationId": "g9png9Tl9s+NOvqkPbVcJw==",
              "IsService": false,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 165495,
      "ConversationsList": [
        {
          "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
          "Conversations": [
            {
              "ChatId": 11355979,
              "UserMsg": "Tuan.",
              "RobotMsg": "Faham, boss! Kadang-kadang nasib memang tak menyebelahi kita. Jangan putus asa, sebab keberuntungan boleh berubah bila-bila masa! Kalau menang besar, boleh cash out banyak! Teruskan bermain, boss! 🍀💪",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 16:41:30",
              "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11355985,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "hi boss ,ade ape yang saya boleh bantu ??☺️",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 16:41:50",
              "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11355992,
              "UserMsg": "saya terlupa masukka. 97901JK ",
              "RobotMsg": "Faham, boss! Jika anda terlupa untuk masukkan JOKER ID semasa top-up, jangan risau! 😊 \n\n📌 Apa yang perlu dilakukan:\n1. Pastikan resit transaksi anda lengkap dan jelas.\n2. Muat naik resit tersebut ke halaman top-up dalam aplikasi seperti biasa.\n3. Tunggu 3-10 minit untuk sistem mengesahkan transaksi.\n\n📌 Untuk lain kali, pastikan anda menulis JOKER ID dalam ruangan \"Recipient Reference\" supaya sistem dapat mengesahkan lebih cepat.\n\nJika ada masalah atau perlukan bantuan, balas saja dalam live chat ya, boss! 🙏🔥",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 16:42:19",
              "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356001,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "ya bos",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 16:42:51",
              "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11356002,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "masa depan jagan lupa ya",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 16:42:58",
              "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11356009,
              "UserMsg": "baik tuan terima kasih. ",
              "RobotMsg": "Sama-sama, boss! 😊 Jika ada apa-apa lagi yang perlu dibantu, jangan segan-segan untuk tanya. Semoga hari anda penuh dengan keberuntungan! 🍀🔥💰",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 16:43:21",
              "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11356015,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Terima Kasih banyak2 bosss❤️",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 16:43:51",
              "ConversationId": "u3P49bUNLRw+iHusXiUqUQ==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 167089,
      "ConversationsList": [
        {
          "ConversationId": "4nXL3TdcUBvv4eFWCZxX3g==",
          "Conversations": [
            {
              "ChatId": 11348058,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hello Bossku ~\r\nSubmit Tadi Ada Kesilapan\r\n\r\n❌Tadi Silap Isi : RM20\r\n✅ Sila Isi : RM25\r\n\r\nSubmit Semula ye ~\r\nThank You Bosskuu ~ ",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 22:18:24",
              "ConversationId": "4nXL3TdcUBvv4eFWCZxX3g==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11348061,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250407/1def427d-ea24-43cf-bc08-7ed94154c818.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 22:18:38",
              "ConversationId": "4nXL3TdcUBvv4eFWCZxX3g==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11348102,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, sila upload slip bank-in melalui (WALLET → TOPUP) ya. 😊\r\n\r\n📌 Proses akan mengambil masa dalam 3-10 minit untuk sistem sahkan transaksi.\r\n📌 Kalau lebih 10 minit masih belum masuk, boleh hantar resit transaksi ke live chat untuk semakan segera.\r\n\r\nTerima kasih boss, mantap! ❤️🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 22:22:36",
              "ConversationId": "4nXL3TdcUBvv4eFWCZxX3g==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11348103,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/operator/20250407/a68f82fe-5488-4617-b6d7-88fe6de8428f.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 22:22:39",
              "ConversationId": "4nXL3TdcUBvv4eFWCZxX3g==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11348104,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 22:22:40",
              "ConversationId": "4nXL3TdcUBvv4eFWCZxX3g==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 167415,
      "ConversationsList": [
        {
          "ConversationId": "ppygoPIndU2+ZrG7dFsHDg==",
          "Conversations": [
            {
              "ChatId": 11349075,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250407/08e1ba73-ff3b-429d-ae5a-8387f1501bce.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:57:20",
              "ConversationId": "ppygoPIndU2+ZrG7dFsHDg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11349081,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, sila upload slip bank-in melalui (WALLET → TOPUP) ya. 😊\r\n\r\n📌 Proses akan mengambil masa dalam 3-10 minit untuk sistem sahkan transaksi.\r\n📌 Kalau lebih 10 minit masih belum masuk, boleh hantar resit transaksi ke live chat untuk semakan segera.\r\n\r\nTerima kasih boss, mantap! ❤️🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:57:48",
              "ConversationId": "ppygoPIndU2+ZrG7dFsHDg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11349090,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "HI Bossku, resit yang sudah CLAIM jangan upload dah ye. Terima Kasih Bossku",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:58:28",
              "ConversationId": "ppygoPIndU2+ZrG7dFsHDg==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 168405,
      "ConversationsList": [
        {
          "ConversationId": "mB2AvJ6MBxT7kLsZtOsKhA==",
          "Conversations": [
            {
              "ChatId": 11348990,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "HI Bossku, resit yang sudah CLAIM jangan upload dah ye. Terima Kasih Bossku",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:49:50",
              "ConversationId": "mB2AvJ6MBxT7kLsZtOsKhA==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11348998,
              "UserMsg": "Sya baru masuk ini",
              "RobotMsg": "Baik, terima kasih kerana berkongsi. Jika ada apa-apa lagi yang perlu dibincangkan, jangan ragu untuk memberitahu ya! Semoga berjaya dan sentiasa mendapat keuntungan yang besar! 🍀🔥💰",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:50:34",
              "ConversationId": "mB2AvJ6MBxT7kLsZtOsKhA==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11349022,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "hi boss ,ade ape yang saya boleh bantu ??☺️",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 23:52:21",
              "ConversationId": "mB2AvJ6MBxT7kLsZtOsKhA==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 169004,
      "ConversationsList": [
        {
          "ConversationId": "rgJrdgS+VRz47qPrgyohrw==",
          "Conversations": [
            {
              "ChatId": 11347742,
              "UserMsg": "apa tdk dpat bnk in pkai fast transfer",
              "RobotMsg": "Hi boss, untuk bank in menggunakan fast transfer, anda boleh menggunakan kaedah Fast Payment (FPX) dalam aplikasi Touch 'n Go eWallet. Dengan FPX, anda boleh memasukkan jumlah yang dikehendaki dan transaksi akan diproses secara automatik dalam masa 1-3 minit. Jadi, anda boleh gunakan kaedah ini untuk bank in dengan lebih cepat. Jika ada sebarang pertanyaan, boleh terus balas di sembang langsung ya boss! 😊🙏",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:47:01",
              "ConversationId": "rgJrdgS+VRz47qPrgyohrw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11347773,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Salam boss! Boleh screenshot hantar supaya saya boleh tengok macam mana transfer tak dapat ya? 😊🙏",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:49:53",
              "ConversationId": "rgJrdgS+VRz47qPrgyohrw==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11347788,
              "UserMsg": "selalu dia,kalau bnk in,trus approved saja dari bnk...ini tdak..lngsung tdak dpat top up",
              "RobotMsg": "Hi boss, jika top up belum masuk, boleh saya tahu boss guna ATM/Transfer (DuitNow) atau Fast Payment (FPX)? Supaya saya boleh bantu semak untuk boss. 😊🙏\n\n📌 Jika guna ATM/Transfer (DuitNow):\n🔹 Pastikan resit sudah diupload ke halaman topup dalam aplikasi.\n🔹 Tunggu 1-10 minit untuk sistem sahkan.\n\n📌 Jika guna Fast Payment (FPX):\n🔹 Biasanya masuk dalam 1-10 minit, kalau lebih 10 minit masih belum masuk, boleh hantar resit transaksi lengkap ke live chat untuk semakan.\n\nJika masih ada masalah, boleh roger kami di live chat untuk bantuan lanjut ya boss! 😊🙏",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:51:05",
              "ConversationId": "rgJrdgS+VRz47qPrgyohrw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11347843,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250407/ce478d3a-e3ef-4340-9b0d-71c30b7de9c1.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:53:43",
              "ConversationId": "rgJrdgS+VRz47qPrgyohrw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11347844,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss 😊\r\n\r\nKalau keluar mesej “Gagal untuk meneruskan”, itu bermaksud sistem Fast Payment mungkin tengah maintenance atau ada gangguan.\r\n\r\n📌 Cara atasi: \r\n1️⃣ Restart phone boss dulu\r\n2️⃣ Tukar sambungan internet (guna WiFi atau data lain)\r\n3️⃣ Kalau masih tak boleh, boss boleh guna kaedah transfer biasa (ATM/Online Banking) dan upload resit seperti biasa\r\n\r\nKalau perlu bantuan, boleh hantar screenshot atau roger saja sini ya boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:53:50",
              "ConversationId": "rgJrdgS+VRz47qPrgyohrw==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11347845,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:53:52",
              "ConversationId": "rgJrdgS+VRz47qPrgyohrw==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        },
        {
          "ConversationId": "p65S/JgduMZBnzG3derRrg==",
          "Conversations": [
            {
              "ChatId": 11347857,
              "UserMsg": "oklh...",
              "RobotMsg": "Sama-sama, boss! Ada lagi pertanyaan atau bantuan yang diperlukan? 😊",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:54:40",
              "ConversationId": "p65S/JgduMZBnzG3derRrg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11347870,
              "UserMsg": "upload resit dekat mana kalau sdah transfer",
              "RobotMsg": "Terima kasih, boss! Jika anda perlu muat naik resit, pastikan resit itu lengkap dan jelas. Resit perlu mempunyai tarikh dan masa transaksi, status ditandakan sebagai \"Berjaya\", jumlah pindahan, dan butiran penerima (akaun bank syarikat kami). Untuk muat naik, gunakan laman atas aplikasi untuk tambah nilai, bukan mesej segera. Selepas muat naik, beri masa 3–10 minit untuk pengesahan sistem. Jika ada masalah, balas mesej ini! 😊🙏",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:56:36",
              "ConversationId": "p65S/JgduMZBnzG3derRrg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11347890,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/operator/20250407/d0838292-958b-43e5-b830-8855021d1ed4.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:58:55",
              "ConversationId": "p65S/JgduMZBnzG3derRrg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11347892,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss, kalau nak upload resit, pastikan ikut langkah ini ya:\r\n\r\n📌 Cara Upload Resit:\r\n1️⃣ Pergi ke halaman topup dalam app.\r\n2️⃣ Pilih kaedah topup yang digunakan (ATM/Transfer atau Fast Payment).\r\n3️⃣ Pilih bank dan masukkan jumlah yang ditopup.\r\n4️⃣ Upload gambar resit transaksi yang jelas & lengkap.\r\n5️⃣ Tekan \"Submit\" dan tunggu 3-10 minit untuk sistem sahkan.\r\n\r\n📌 Kalau lebih 10 minit masih belum masuk, boleh hantar resit ke live chat untuk semakan segera.\r\n\r\nKalau ada pertanyaan lain, boleh roger kami di live chat ya boss! 😊🙏",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:59:04",
              "ConversationId": "p65S/JgduMZBnzG3derRrg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11347893,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 21:59:06",
              "ConversationId": "p65S/JgduMZBnzG3derRrg==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 170514,
      "ConversationsList": [
        {
          "ConversationId": "oMI54ReZZNitSabLlesXBg==",
          "Conversations": [
            {
              "ChatId": 11345502,
              "UserMsg": "kredit tak masuk lagi nie",
              "RobotMsg": "Hi boss, jika kredit masih belum masuk, boleh saya tahu lebih lanjut bagaimana anda melakukan top up tersebut? Adakah melalui ATM/Transfer (DuitNow) atau Fast Payment (FPX)? Dengan maklumat tersebut, saya boleh membantu menyiasat masalah ini untuk anda. Terima kasih! 😊🙏",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:08:37",
              "ConversationId": "oMI54ReZZNitSabLlesXBg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11345506,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "resit send sini jab",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:09:03",
              "ConversationId": "oMI54ReZZNitSabLlesXBg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11345507,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss ,resit kali ini sama resit dengan tadi boss yg upload ya , cuba check wallet anda ya 😊\r\n",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:09:17",
              "ConversationId": "oMI54ReZZNitSabLlesXBg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11345510,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250407/8a79cec8-e62a-4d6b-b977-a0c6350345b1.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:09:30",
              "ConversationId": "oMI54ReZZNitSabLlesXBg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11345511,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Terima kasih boss! 😊 Kalau dah upload, sila tunggu 3-10 minit untuk sistem sahkan transaksi.\r\n\r\n📌 Kalau lebih 10 minit masih belum masuk, boleh hantar resit transaksi ke live chat untuk semakan segera.\r\n\r\nTerima kasih atas kesabaran boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:09:58",
              "ConversationId": "oMI54ReZZNitSabLlesXBg==",
              "IsService": true,
              "AdminAction": 0
            },
            {
              "ChatId": 11345512,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "--- Tamat Perbualan ---",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:10:00",
              "ConversationId": "oMI54ReZZNitSabLlesXBg==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 170674,
      "ConversationsList": [
        {
          "ConversationId": "O59KLxXol5O/tx73mpC2Pg==",
          "Conversations": [
            {
              "ChatId": 11345842,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250407/9be6dbd3-4f3c-49a2-9823-438113cfea29.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:41:49",
              "ConversationId": "O59KLxXol5O/tx73mpC2Pg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11345847,
              "UserMsg": "knp lambat masuk",
              "RobotMsg": "Saya faham, boss. Kalau lambat masuk, mungkin terdapat beberapa sebab seperti masalah rangkaian internet atau maintenance pada platform permainan. Anda boleh cuba tutup semula aplikasi permainan, tukar rangkaian internet, atau tunggu sehingga maintenance selesai. Jika masih menghadapi masalah, anda boleh cuba guna VPN atau hantar screenshot ke live chat untuk bantuan lanjut. Semoga masalah dapat diselesaikan dengan cepat! 😊👍",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:42:01",
              "ConversationId": "O59KLxXol5O/tx73mpC2Pg==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11345852,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Terima kasih boss! 😊 Kalau dah upload, sila tunggu 3-10 minit untuk sistem sahkan transaksi.\r\n\r\n📌 Kalau lebih 10 minit masih belum masuk, boleh hantar resit transaksi ke live chat untuk semakan segera.\r\n\r\nTerima kasih atas kesabaran boss! 🙏🔥",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-07 18:42:17",
              "ConversationId": "O59KLxXol5O/tx73mpC2Pg==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },
    {
      "MemberId": 171682,
      "ConversationsList": [
        {
          "ConversationId": "FZaDqM9Cn+VpZ/1Jw8aFpw==",
          "Conversations": [
            {
              "ChatId": 11360741,
              "UserMsg": "j3 kena ibox rm2 2nd price bila masuk duit ye",
              "RobotMsg": "Hi boss, J3 winnings akan dikreditkan ke dalam dompet anda secara automatik. Sila bersabar ya, sistem sedang memproses. 😊💰\n\n📌 Anda boleh semak di bahagian \"Report\" antara 10:00 PM - 10:30 PM untuk melihat kredit tersebut.\n\nTerima kasih atas kesabaran anda, boss, dan semoga anda dapat HUAT yang besar! 🔥🍀",
              "AdminReply": "",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:19:47",
              "ConversationId": "FZaDqM9Cn+VpZ/1Jw8aFpw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11360772,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "",
              "ImgUrl": "https://joker2api728.com/cdnimg/joker2020/chatService/member/20250408/a31f7e31-b126-411c-84aa-3fcfd7355681.jpg",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:20:36",
              "ConversationId": "FZaDqM9Cn+VpZ/1Jw8aFpw==",
              "IsService": false,
              "AdminAction": 0
            },
            {
              "ChatId": 11360959,
              "UserMsg": "",
              "RobotMsg": "",
              "AdminReply": "Hi boss 😊\r\n\r\nSabar sikit ya, sistem tengah proses kemenangan boss.\r\nHari ni duit menang masuk agak lambat sikit, tapi confirm akan masuk juga 💰\r\nTerima kasih atas kesabaran boss! 🍀",
              "ImgUrl": "",
              "ReplyChatId": 0,
              "CreateDate": "2025-04-08 22:25:32",
              "ConversationId": "FZaDqM9Cn+VpZ/1Jw8aFpw==",
              "IsService": true,
              "AdminAction": 0
            }
          ]
        }
      ]
    },

Você deve extrair e transformar essa conversa para o seguinte formato (em JSON):
Answer: solution
Question: problem
intent: intent



{
  "id": "",
  "question": {
    "text": "Boss, I want to top up Mega",
    "variations": [
      "Bos, saya nak topup Mega",
      "Boss, I want to top up Mega",
      "老闆，我想充值Mega"
    ],
    "intent": "top_up_inquiry",
    "languages": {
      "en": "\"How to top up Mega?\"",
      "ms": "\"Mcm mn nak top up mega\"",
      "cn": "\"怎麼充值Mega？\""
    }
  },
  "answer": {
    "detailed": {
      "en": "\"Hi boss, to top up, follow these steps: ...\"",
      "ms": "\"Hi boss, nak topup boleh ikut langkah ini: ...\"",
      "cn": "\"嗨，老闆，想充值請按以下步驟：...\""
    },
    "conditions": []
  },
  "metadata": {
    "category": [
      "finance"
    ],
    "subCategory": "top_up_inquiry",
    "difficulty": 2,
    "confidence": 0.5,
    "dateCreated": "2025-03-03T03:24:31Z",
    "lastUpdated": "2025-03-03T03:24:31Z",
    "version": "1.0",
    "source": "",
    "status": "active"
  },
  "context": {
    "relatedTopics": [],
    "prerequisites": [],
    "followUpQuestions": {
      "en": [],
      "ms": [],
      "cn": []
    }
  },
  "usage": {
    "searchFrequency": 0,
    "successRate": 0,
    "lastQueried": null
  },
  "review_status": []
}

A ideia é que a parte da conversa em que o cliente relata seu problema seja convertida para "question" (que pode ser aprimorada se estiver muito resumida) e a resposta do atendimento seja convertida para "answer". Além disso, você deve extrair ou definir a "intent" da pergunta.

Converta a conversa mantendo a mesma ordem da comunicação.

Forneça o resultado final em JSON.
"""

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
        model="gpt-3.5-turbo",
          messages=[
            {
                "role": "system",
                "content": "You are an AI assistant evaluating answers to user questions.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=250,
        temperature=0.1,
    )

# Exiba a resposta
result = response.choices[0].message["content"].strip()
print(result)