# NCRP UNIFIED MASTER AGENT (एकीकृत साइबर अपराध अन्वेषण मास्टर एजेंट)
**Cyber Police Station, North District, Delhi Police**

---

### 🇮🇳 हिंदी निर्देश (Quick Guide in Hindi)

अब आपके सभी 10 अलग-अलग एजेंट्स को **एक ही मास्टर एजेंट (`ncrp_master_agent.py`)** में मर्ज (एकीकृत) कर दिया गया है। आपको अलग-अलग फाइलों या एजेंटों में उलझने की बिल्कुल जरूरत नहीं है।

#### इसमें कौन-कौन से कार्य एक साथ होते हैं:
1. **Complaint Examination & Dossier**: NCRP Complaint PDF को स्कैन करना, शिकायतकर्ता की जानकारी, फ्रॉड रकम निकालना और दिल्ली पुलिस के 14 स्टैंडर्ड फोल्डर तैयार करना।
2. **Forensic Money Trail**: 5-Sheet Master Excel तैयार करना, 3D Flowchart (PNG/JPG) और 3D Interactive Web Visualizer बनाना।
3. **Bank Statutory Notices (Section 94 BNSS)**: हर बैंक का अलग नोटिस (Single-Bank Isolation), 5 दिन के IP Login लॉग्स और ATM CCTV फुटेज रिक्विजिशन (Signed & Unsigned, Word और PDF)।
4. **Telecom CDR & SDR**: संदिग्ध मोबाइल नंबरों के लिए Airtel, Jio, Vi आदि को CDR/SDR/CAF नोटिस।
5. **IPDR Forensics**: इंटरनेट सर्विस प्रोवाइडर (ISP) को NAT IPDR और भौतिक पते के लिए नोटिस।
6. **Big Tech (Google & Meta)**: Gmail, Instagram, WhatsApp के लिए 90-दिन का रिकॉर्ड प्रिजर्वेशन व LERS नोटिस।
7. **Suspect Intelligence DB**: सभी म्यूल खातों और संदिग्ध नंबरों को SQLite डेटाबेस में रिकॉर्ड करना।
8. **Police Case Diary (Zimni)**: धारा 192 BNSS के तहत दैनिक केस डायरी / ज़िमनी तैयार करना (Signed & Unsigned)।
9. **Email Dispatch Manifest**: नोडल अधिकारियों के ईमेल तैयार करना।
10. **OSINT & 15.6M Cell Tower Engine**: सेल आईडी और टॉवर लोकेशन प्राप्त करना।

---

### इसे कैसे इस्तेमाल करें (How to Run):

#### तरीका 1: सबसे आसान तरीका (1-Click Run)
- बाहर दिए गए **`RUN_NCRP_MASTER_AGENT.bat`** पर डबल क्लिक करें।
- मेनू खुलेगा, जहाँ आप `1` दबाकर तुरंत पूरी जांच चला सकते हैं।

#### तरीका 2: किसी नई कंप्लेंट PDF को जांचना
- अपनी नई NCRP Complaint PDF को `NCRP_Master_Agent\input\` फोल्डर में डालें।
- कमांड प्रॉम्प्ट में चलाएं:
  ```bash
  python NCRP_Master_Agent\ncrp_master_agent.py --case <ACKNOWLEDGEMENT_NO>
  ```
  या
  ```bash
  python NCRP_Master_Agent\ncrp_master_agent.py --pdf "NCRP_Master_Agent\input\your_file.pdf"
  ```

#### सभी आउटपुट कहाँ मिलेंगे:
- सारा रिजल्ट **`NCRP_Master_Agent\output\Case_<ACK_NO>\`** के अंदर मिलेगा:
  - `BankAction_CompleteTrail_<ACK_NO>.xlsx` (मास्टर एक्सेल)
  - `forensic_money_trail_3d_<ACK_NO>.png / .jpg` (3D फ्लोचार्ट)
  - `money_trail_3d_visualizer_<ACK_NO>.html` (3D इंटरैक्टिव ग्राफ)
  - `Individual_Notices_<ACK_NO>\` (सभी बैंकों, टेलीकॉम, गूगल, इंस्टाग्राम के साइन किए हुए नोटिस)
  - `Case_Diaries\` (साइन की हुई पुलिस केस डायरी / ज़िमनी)
  - `Investigation_Dossier\` (14 पुलिस फोल्डर)

---

### Folder Structure (संरचना)
```
NCRP Compalint Againt/
│
├── RUN_NCRP_MASTER_AGENT.bat   <-- [1-Click Launcher]
│
└── NCRP_Master_Agent/          <-- [आपका एकलौता मास्टर एजेंट फोल्डर]
    ├── ncrp_master_agent.py    <-- सभी 10 एजेंटों का एक मास्टर कोड
    ├── api_server.py           <-- REST API सर्वर
    ├── run_agent.bat           <-- डायरेक्ट बैटरनर
    ├── input/                  <-- अपनी NCRP Complaint PDF यहाँ रखें
    ├── output/                 <-- सारे नोटिस, एक्सेल, केस डायरी यहाँ बनती हैं
    ├── templates/              <-- सभी वर्ड नोटिस और केस डायरी के फॉर्मेट्स
    ├── assets/                 <-- दिल्ली पुलिस का लोगो, मुहर, हस्ताक्षर, बैंक लोगो
    ├── config/                 <-- कॉन्फ़िगरेशन और नोडल अधिकारियों की डायरेक्टरी
    └── database/               <-- साइबर इंटेलिजेंस डेटाबेस
```


---

### 📧 नया फीचर: स्वचालित ईमेल प्रेषण एजेंट (Email Dispatch Agent)

अब सिस्टम में एक समर्पित **Email Dispatch Agent (`email_dispatch_agent.py`)** जोड़ दिया गया है।

#### मुख्य विशेषताएं (Key Capabilities):
1. **ईमेल बॉडी में नोटिस + PDF अटैचमेंट**:
   - जनरेट किए गए नोटिस का पूरा प्रारूप (रेफरेंस नंबर, धारा 94 BNSS, बैंक खातों की टेबल व हस्ताक्षर) ईमेल की बॉडी में ऑफिशियल HTML रूप में जाता है।
   - साथ में उस नोटिस की ओरिजिनल PDF फाइल अटैच होकर जाती है।
2. **15 सेकंड का अनिवार्य अंतराल (Rate Limiting)**:
   - हर एक मेल भेजने के बाद सिस्टम 15 सेकंड का लाइव काउंटडाउन पॉज लेता है ताकि ईमेल सर्वर (Gmail / NIC) द्वारा स्पैम या रेट-लिमिट ब्लॉक न लगे।
3. **मल्टी-प्रोवाइडर सपोर्ट (Outlook, Gmail व NIC Mail)**:
   - **Microsoft Outlook**: `cyberinvestigationdelhipolice@outlook.com` से सीधे `smtp-mail.outlook.com:587` के जरिए।
   - **Google Gmail**: Google OAuth2 (Client ID & Client Secret) तथा Gmail App Password (SMTP) दोनों समर्थित।
   - **NIC Mail (`mail.gov.in` / `smtp.delhipolice.gov.in`)**: Kavach 2FA App Password के साथ सुरक्षित ऑटोमेशन समर्थित।
4. **फॉरवर्डिंग मोड (Outlook / Gmail -> NIC Mail)**:
   - सभी नोटिसों को एक-एक करके 15 सेकंड के गैप पर थाने की NIC मेल आईडी (`rajendra.28082016@delhipolice.gov.in`) पर फॉरवर्ड किया जाता है।
5. **डायरेक्ट 1-क्लिक रनर**:
   - बाहर दिए गए **`RUN_EMAIL_DISPATCH_AGENT.bat`** पर डबल क्लिक करके सीधे टेस्ट ईमेल या केस नोटिस भेजे जा सकते हैं।

#### क्रेडेंशियल सेटिंग्स फ़ाइल:
- `NCRP_Master_Agent\config\email_credentials.json` में अपनी Client ID, Client Secret या App Password दर्ज करें।
