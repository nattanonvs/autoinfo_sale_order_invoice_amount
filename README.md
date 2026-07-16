# AutoInfo Sale Order Invoice Amount (Odoo 15)

โมดูลนี้เป็นโมดูลเสริมของ `sale_order_invoice_amount` (OCA)

โมดูลนี้ช่วยดูยอดวางบิล ยอดรับชำระ และสถานะการเก็บเงินบนเอกสารขาย

## ขอบเขต

- ใช้กับ `Quotation`
- ใช้กับ `Sales Order`
- ใช้กับ invoice ที่เชื่อมกับเอกสารขาย

## คุณสมบัติ

- เพิ่มฟิลด์ใหม่บน `sale.order`
  - Invoiced Untaxed Amount
  - Uninvoiced Untaxed Amount
  - Invoiced Amount (%)
- แสดงค่าบน Sale Order Form และ Tree view
- เพิ่ม Smart Button `Collections` บน Sale Order เพื่อเปิดหน้าสรุปการเก็บเงินและรายการ Invoice ที่เกี่ยวข้อง
- เพิ่ม `Collection Status` สำหรับติดตามสถานะ `Partial Collection`, `Fully Collected`, และ `Closed Agreement`
- แสดง `Collection Status` ได้ทั้งบนหน้า Form, Tree view และ Search filters
- รองรับ workflow `Close Agreement` แบบใหม่ โดยต้องกรอกทั้งเหตุผลและยอดตามสัญญาที่ต้องการยกเลิกก่อนยืนยัน
- แสดงสรุปสัญญาบนหน้า Sale Order และหน้า `Collections` ครบ 5 ค่า: ยอดเต็มของสัญญา, ยอดที่ต้องได้รับ, ยอดที่เก็บแล้ว, ยอดที่ยังไม่ได้เก็บ, และยอดที่ยกเลิก
- รองรับ `Reopen Agreement` โดยให้ `Sales Manager` และ `Settings` (`base.group_system`) เปิดกลับได้ และล้างข้อมูลการปิดสัญญาเดิมออกทั้งหมด
- ผู้ใช้ `Settings` (`base.group_system`) สามารถ `Close Agreement` และ `Reopen Agreement` ได้ข้ามแผนก
- แยกติดตั้ง/ถอนการติดตั้งได้ โดยไม่กระทบโมดูลหลักของ Odoo (มีผลเฉพาะการเพิ่ม field และ view ของโมดูลนี้)

## Dependency

- `sale_order_invoice_amount`
- `sale_margin`
- `account`

## ติดตั้งแบบย่อ

1. วางโฟลเดอร์โมดูลไว้ที่ `/var/odoo/custom15_autoinfo/autoinfo_sale_order_invoice_amount`
2. ตรวจว่า path นี้อยู่ใน `addons_path`
3. รีสตาร์ต Odoo
4. ไปที่ `Apps`
5. กด `Update Apps List`
6. ค้นหา `AutoInfo Sale Order Invoice Amount`
7. กด `Install`

path หลักที่ใช้ในเอกสารชุดนี้คือ:

`/var/odoo/custom15_autoinfo`

## เอกสาร

- คู่มือใช้งาน: `docs/user_guide.md`
- คู่มือเทคนิค: `docs/technical_guide.md`
- วิธีแก้ปัญหา: `docs/troubleshooting.md`
- ประวัติการเปลี่ยนแปลง: `docs/timeline_changelog.md`

## Ownership

- Original Owner: ForgeFlow, Odoo Community Association (OCA)
- Extended By: The Auto-Info Co., Ltd.

## Changelog Summary

- เพิ่มหน้า `Collections`
- เพิ่มสถานะการเก็บเงิน
- เพิ่ม `Close Agreement` และ `Reopen Agreement`
- เพิ่มการบังคับกรอก `Cancelled Amount` ใน `Close Agreement`
- เพิ่ม `Contract Summary` สำหรับติดตามยอดเต็ม, ยอดคาดรับ, ยอดเก็บแล้ว, ยอดค้าง และยอดยกเลิก
- เพิ่มสิทธิ์ `Settings` (`base.group_system`) ให้ปิด/เปิดสัญญาได้ข้ามแผนก
- แก้ปัญหาเรื่อง currency และ view modifier
- เพิ่มคอลัมน์ในหน้า list และปรับ smart button

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.
AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight.
