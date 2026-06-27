# วิธีแก้ปัญหา

## 1. หาโมดูลไม่เจอใน Apps

ทำตามนี้ทีละข้อ

1. ตรวจว่า path `/var/odoo/custom15_autoinfo` อยู่ใน `addons_path`
2. รีสตาร์ต Odoo
3. ไปที่ `Apps`
4. กด `Update Apps List`
5. ค้นหาโมดูลใหม่อีกครั้ง

## 2. กดเข้าโมดูลแล้ว view พัง

อาการที่อาจเจอ

- เปิดหน้าแล้ว error
- กดปุ่มแล้วเด้ง
- หน้า tree หรือ form ไม่ขึ้น

ให้ทำตามนี้

1. อัปเกรดโมดูล
2. รีเฟรชหน้าเว็บแบบแรง 1 ครั้ง
3. ตรวจว่า dependency ติดตั้งครบแล้ว

dependency หลักคือ

- `sale_order_invoice_amount`
- `sale_margin`
- `account`

## 3. ปุ่ม Collections ขึ้น แต่ยอดไม่ตรง

ให้ตรวจตามนี้

1. invoice ต้องไม่เป็นสถานะยกเลิก
2. invoice ควรโพสต์แล้ว
3. ถ้ามีการรับเงินแล้ว ให้ตรวจว่ายอดค้างใน invoice ลดลงแล้ว
4. เปิดเอกสารใหม่อีกครั้งหลังรับเงิน

## 4. หน้า Collections ไม่มีรายการ invoice

ให้ตรวจตามนี้

1. Sale Order ต้องเชื่อมกับ invoice จริง
2. invoice ที่ถูกยกเลิกจะไม่ถูกเอามาแสดง
3. ถ้าเพิ่งสร้าง invoice ให้รีเฟรชหน้าอีกครั้ง

## 5. เปอร์เซ็นต์ขึ้นผิด

ถ้าเห็นเลขมากเกินจริง เช่น `10000%`

สาเหตุคือ

- widget เปอร์เซ็นต์ของ Odoo ต้องใช้ค่าแบบส่วน เช่น `1.00`

ตอนนี้โมดูลนี้ล็อกไว้แล้วไม่ให้เกิน `100.00%`

## 6. กด Close Agreement ไม่ได้

ให้ตรวจตามนี้

1. ต้องใส่เหตุผลก่อนกด `Confirm`
2. ผู้ใช้ต้องมีสิทธิ์ในงานขาย
3. ถ้าระบบใช้แผนก ผู้ใช้ต้องอยู่แผนกที่ตรงกับเอกสาร

## 7. ไม่เห็นปุ่ม Close Agreement

ให้ตรวจตามนี้

1. ผู้ใช้ต้องเปิดเอกสารขายได้ก่อน
2. ถ้าเอกสารถูกปิดแล้ว ระบบจะซ่อนปุ่ม `Close Agreement`
3. เมื่อปิดแล้ว ระบบจะโชว์ `Reopen Agreement` แทน

## 8. ไม่เห็นปุ่ม Reopen Agreement

ให้ตรวจตามนี้

1. ปุ่มนี้ใช้ได้เฉพาะ `Sales Manager`
2. เอกสารต้องอยู่ในสถานะ `Closed Agreement` ก่อน

## 9. อัปเกรดโมดูลแล้ว error เรื่อง currency หรือ state

โมดูลนี้แก้ไว้แล้วสำหรับ 2 เรื่องนี้

1. กรณี currency ยังไม่พร้อมระหว่าง recompute
2. กรณี field `state` ต้องมีใน tree ย่อยของ invoice

ถ้ายังเจออีก

1. คัดลอกไฟล์เวอร์ชันล่าสุดขึ้น server
2. อัปเกรดโมดูลอีกครั้ง
3. ล้าง cache หน้าเว็บ

## 10. ถ้ายังแก้ไม่ได้

ให้เก็บข้อมูลนี้ไว้

1. ชื่อฐานข้อมูล
2. ชื่อโมดูล
3. เวอร์ชันใน `__manifest__.py`
4. ข้อความ error เต็ม
5. ขั้นตอนก่อนเกิดปัญหา

แล้วส่งให้ผู้ดูแลระบบตรวจต่อ

## ข้อจำกัดที่ควรรู้

- ถ้าข้อมูล invoice หรือ payment ยังไม่สมบูรณ์ ยอดที่เห็นก็จะยังไม่สมบูรณ์
- ถ้าสิทธิ์ผู้ใช้หรือข้อมูลแผนกไม่ถูกต้อง ปุ่มบางปุ่มอาจไม่ขึ้น

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.

AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight.
