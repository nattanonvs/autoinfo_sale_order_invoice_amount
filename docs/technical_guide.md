# คู่มือเทคนิค

## โมดูลนี้ทำอะไร

โมดูลนี้เป็นโมดูลเสริม

โมดูลนี้ต่อจากโมดูลเดิมชื่อ `sale_order_invoice_amount`

โมดูลนี้เพิ่มเรื่อง

- หน้า `Collections`
- สถานะการเก็บเงิน
- ปุ่ม `Close Agreement`
- ปุ่ม `Reopen Agreement`

## ติดตั้ง

1. วางโฟลเดอร์โมดูลไว้ที่
   `/var/odoo/custom15_autoinfo/autoinfo_sale_order_invoice_amount`
2. ตรวจว่า path หลักนี้อยู่ใน `addons_path`
   `/var/odoo/custom15_autoinfo`
3. รีสตาร์ต Odoo
4. ไปที่ `Apps`
5. กด `Update Apps List`
6. ค้นหา `AutoInfo Sale Order Invoice Amount`
7. กด `Install`

## อัปเดตเวอร์ชัน

1. คัดลอกไฟล์ใหม่ทับไฟล์เดิม
2. รีสตาร์ต Odoo
3. อัปเกรดโมดูล

ตัวอย่างคำสั่ง

1. เปิด terminal
2. รันคำสั่งอัปเกรดโมดูล

```bash
./odoo-bin -c /etc/odoo/odoo.conf -d <database_name> -u autoinfo_sale_order_invoice_amount --stop-after-init
```

## ถอนการติดตั้ง

1. ไปที่ `Apps`
2. ค้นหาโมดูลนี้
3. กด `Uninstall`

หลังจากถอน

- field และ view ของโมดูลนี้จะถูกเอาออกจาก registry
- โมดูลหลักของ Odoo จะไม่ถูกลบ

## โครงสร้างหลัก

- `__manifest__.py` เก็บข้อมูลโมดูล
- `models/` เก็บ logic ฝั่ง Python
- `wizard/` เก็บหน้าต่างป๊อปอัปปิดข้อตกลง
- `views/` เก็บ form, tree, search และ wizard view
- `security/` เก็บสิทธิ์การใช้ wizard
- `docs/` เก็บเอกสาร

## ไฟล์สำคัญ

- `models/sale_order.py`
- `models/account_move.py`
- `wizard/close_agreement_wizard.py`
- `views/sale_order_view.xml`
- `views/close_agreement_wizard_views.xml`
- `security/ir.model.access.csv`

## Dependency

โมดูลนี้ใช้ dependency หลักดังนี้

- `sale_order_invoice_amount`
- `sale_margin`
- `account`

## หมายเหตุทางเทคนิค

- ยอดเก็บเงินคำนวณจาก invoice ที่เชื่อมกับ sale order
- invoice ที่ถูกยกเลิกจะไม่ถูกนำมาคิด
- ถ้า currency ของเอกสารยังไม่พร้อม ระบบจะใช้ fallback currency ที่ปลอดภัย
- tree ย่อยของ invoice มี field `state` แบบซ่อน เพื่อให้ modifier ของ Odoo ทำงานถูกต้อง
- `Close Agreement` จะตรวจสิทธิ์ผู้ใช้ก่อนทุกครั้ง และ `base.group_system` สามารถข้ามข้อจำกัดแผนกได้
- `Reopen Agreement` ใช้ได้สำหรับ `Sales Manager` และ `base.group_system`

## ฟิลด์และตรรกะใหม่

- ฟิลด์ใหม่บน `sale.order`
  - `closed_agreement_cancel_amount`
  - `contract_expected_amount`
  - `contract_uncollected_amount`
- ฟิลด์ใหม่บน wizard `close.agreement.wizard`
  - `currency_id`
  - `cancel_amount`
  - `cancel_amount_provided`
- `contract_expected_amount` คำนวณจาก `amount_total - closed_agreement_cancel_amount`
- `contract_uncollected_amount` คำนวณจาก `contract_expected_amount - total_paid_amount`
- เมื่อ `Reopen Agreement` ระบบจะล้าง `is_closed_agreement`, เหตุผล, วันเวลา, ผู้ปิด และ `closed_agreement_cancel_amount`

## Validation ใหม่ของ Close Agreement

- ต้องกรอก `reason`
- ต้องมีการส่งค่า `cancel_amount` เข้ามาจริง
- `cancel_amount` ต้องไม่ติดลบ
- `cancel_amount` ต้องไม่มากกว่ายอดค้าง ณ เวลาที่กดปิด (`amount_total - total_paid_amount`)
- ฝั่ง wizard จะเรียก `_check_close_agreement_access()` ก่อนบันทึกข้อมูลเสมอ

## การอัปเดต View ที่เกี่ยวข้อง

- ฟอร์ม wizard เพิ่มช่อง `Cancelled Amount`
- ส่วนหัวของ Sale Order เพิ่มสิทธิ์ให้ `base.group_system` เห็นปุ่ม `Close Agreement` และ `Reopen Agreement`
- หน้า Sale Order และหน้า `Collections` แสดง `Contract Summary`
- หน้า `Collections` แสดง `closed_agreement_cancel_amount` เมื่อเอกสารถูกปิดสัญญาแล้ว

## การทดสอบที่ควรทำหลังติดตั้ง

1. เปิดหน้า `Quotation`
2. เปิดหน้า `Sales Order`
3. เปิดหน้า `Collections`
4. ลองกด `Close Agreement` พร้อมกรอกเหตุผลและยอดยกเลิก
5. ทดสอบกรณียอดยกเลิกมากกว่ายอดค้างเพื่อยืนยัน validation
6. ลองกด `Reopen Agreement` ด้วย `Sales Manager` หรือ `Settings`
7. ดูคอลัมน์ในหน้า list และตรวจสรุปสัญญาบนหน้า `Collections`

## ถ้าจะย้ายขึ้น Git

1. ตรวจ version ใน `__manifest__.py`
2. ตรวจ changelog
3. สร้าง zip backup
4. ตรวจชื่อ repo ให้ตรงกับชื่อโมดูล

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon – Project conception, implementation, and thorough review of all deliverables.

AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight.
