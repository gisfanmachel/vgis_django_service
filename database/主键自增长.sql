select setval('tt_group_accident_insurance_standing_book_id_seq',(select max(id)+1 from tt_group_accident_insurance_standing_book),false);
select setval('tt_insruance_type_id_seq',(select max(id)+1 from tt_insruance_type),false);
select setval('tt_insuance_email_information_id_seq',(select max(id)+1 from tt_insuance_email_information),false);
select setval('tt_insurance_email_attachment_id_seq',(select max(id)+1 from tt_insurance_email_attachment),false);
select setval('tt_insurance_standing_book_id_seq',(select max(id)+1 from tt_insurance_standing_book),false);
select setval('tt_insured_people_information_id_seq',(select max(id)+1 from tt_insured_people_information),false);
select setval('tt_zh-unit_id_seq',(select max(unit_id)+1 from tt_zh-unit_id),false);