/**
 * Google Apps Script for NCRP Master Agent - Centralized Mule Account Database
 * Delhi Police Cyber Crime Investigation Unit
 *
 * Instructions:
 * 1. Open your Google Drive (with gkncyber1262@gmail.com).
 * 2. Create a new Google Sheet named: "म्यूल अकाउंट डेटाबेस" (or Mule Account Database).
 * 3. In the top menu, click: Extensions (एक्सटेंशन) -> Apps Script.
 * 4. Delete any existing code, paste this entire file, and click Save (Ctrl + S).
 * 5. Click "Deploy" (तैनात करें) -> "New deployment" (नया डिप्लॉयमेंट).
 * 6. Select type: "Web app" (वेब ऐप).
 *    - Description: "NCRP Mule Sync"
 *    - Execute as: "Me" (gkncyber1262@gmail.com)
 *    - Who has access: "Anyone" (कोई भी)
 * 7. Click "Deploy" and authorize permissions.
 * 8. Copy the Web app URL (starts with https://script.google.com/macros/s/...)
 * 9. Paste this URL into NCRP_Master_Agent/config/google_sheets_config.json under "apps_script_webhook_url"
 *    OR send in Telegram bot using: /setsheeturl <YOUR_URL>
 */

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.tryLock(15000);

  try {
    var contents = JSON.parse(e.postData.contents);
    var action = contents.action || "append_rows";
    var rows = contents.rows || [];
    var headers = contents.headers || [
      "Acknowledgement / FIR No.",
      "Complainant Name",
      "Complainant Address",
      "Complainant Mobile",
      "Layer",
      "Bank Name",
      "Suspect Account No.",
      "IFSC Code",
      "Bank Branch Address",
      "Cheated / Disputed Amount (₹)",
      "Brief Facts of Complaint",
      "Total Defrauded Amount (₹)",
      "Total Lien / Hold Amount (₹)",
      "Investigating Officer (IO)",
      "Record Timestamp"
    ];

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheetName = contents.sheet_tab || "Mule_Accounts";
    var sheet = ss.getSheetByName(sheetName);

    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
    }

    // Set headers if new
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(headers);
      var headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setBackground("#1E3A8A"); // Navy blue
      headerRange.setFontColor("#FFFFFF");
      headerRange.setFontWeight("bold");
      headerRange.setFontFamily("Arial");
      headerRange.setHorizontalAlignment("center");
      sheet.setFrozenRows(1);
    }

    // Get existing keys to prevent duplicates
    var existingKeys = {};
    var lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      var data = sheet.getRange(2, 1, lastRow - 1, 8).getValues();
      for (var i = 0; i < data.length; i++) {
        var k = String(data[i][0]).trim() + "_" + String(data[i][4]).trim() + "_" + String(data[i][6]).trim() + "_" + String(data[i][7]).trim();
        existingKeys[k] = true;
      }
    }

    var addedCount = 0;
    for (var j = 0; j < rows.length; j++) {
      var r = rows[j];
      var rowKey = String(r[0] || "").trim() + "_" + String(r[4] || "").trim() + "_" + String(r[6] || "").trim() + "_" + String(r[7] || "").trim();
      if (!existingKeys[rowKey]) {
        sheet.appendRow(r);
        existingKeys[rowKey] = true;
        addedCount++;
      }
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      added_rows: addedCount,
      total_rows_received: rows.length,
      spreadsheet_url: ss.getUrl()
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  return ContentService.createTextOutput(JSON.stringify({
    status: "active",
    spreadsheet_name: ss.getName(),
    spreadsheet_url: ss.getUrl(),
    message: "Delhi Police Cyber Crime Mule Database Webhook is Running!"
  })).setMimeType(ContentService.MimeType.JSON);
}
