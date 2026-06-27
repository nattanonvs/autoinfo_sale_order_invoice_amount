# คู่มือติดตั้ง (Odoo 15)

## 1) เตรียมไฟล์โมดูล

คัดลอกโฟลเดอร์ `autoinfo_sale_order_invoice_amount/` ไปไว้ใน addons path ของ Odoo

หมายเหตุ: บน Linux server โดยทั่วไปนิยมใช้ path `/var/odoo/custom15_autoinfo` และต้องอยู่ใน `addons_path` ของไฟล์ config

## 2) อัปเดตรายการแอป (Update Apps List)

เข้า Odoo → Apps → Update Apps List

## 3) ติดตั้งโมดูล

ค้นหา “AutoInfo Sale Order Invoice Amount” แล้วกด Install

## 4) ตรวจสอบผลลัพธ์

- ไปที่ Sales → Orders → Quotation / Sales Order
- เปิดเอกสาร 1 ใบ จะเห็นบล็อกแสดงค่า:
  - Invoiced Untaxed Amount
  - Uninvoiced Untaxed Amount
  - Invoiced Amount (%)

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.
AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight (e.g., suggesting code snippets and optimizations).
