# PD-004 · VALUE AND SUCCESS METRICS

**Project ID:** FATHER-ACADEMY-OSINT-001  
**Status:** DRAFT

## 1. North-star product result

Не количество загруженных документов и не размер RAG.

Главный результат:

> агент после обучения выполняет проверяемую профессиональную задачу лучше, чем до обучения, а изменение компетенции подтверждается воспроизводимыми evidence и evaluation.

## 2. MVP success metrics

### M-001 Training Completion
Полный учебный цикл может быть завершён без ручного переписывания состояния между этапами.

Target prototype: **1 полный воспроизводимый цикл**.

### M-002 Evidence Coverage
Каждая оцениваемая работа имеет evidence/source references.

Target: **100% оцениваемых результатов**.

### M-003 Skill Traceability
Каждое изменение mastery_score связано с конкретным Evaluation.

Target: **100% изменений mastery_score**.

### M-004 Error Detection
Evaluator обнаруживает заранее подготовленные ошибки.

Target: **PASS on controlled error set**.

### M-005 Retraining Effect
После разбора ошибки агент получает корректирующее задание/процедуру и проходит повторную проверку.

Target: **минимум 1 доказанный correction loop**.

### M-006 Restart Recovery
После перезапуска сохраняются curriculum, assignment, training run, evidence, evaluation и SkillProfile.

Target: **воспроизводимое восстановление состояния**.

### M-007 Source Provenance
Каждый knowledge claim, используемый в оценке, имеет проверяемый SourceDocument/SourceFragment или явно помечен как unverified.

Target: **100% критичных утверждений**.

### M-008 Competence Separation
Система не повышает mastery_score за наличие документа/RAG-записи без практической проверки.

Target: **0 ложных повышений в acceptance test**.

### M-009 Reuse Readiness
Модель Profession→Competency→Skill→Assignment→Evaluation не содержит жёсткой логики только для Telegram.

Target: **можно описать второй учебный кейс без изменения core schema**.

## 3. Guardrail metrics

- autonomous_prohibited_action_count = 0;
- untraceable_mastery_update_count = 0;
- unsupported_source_promotion_count = 0;
- secret/session leakage to repository = 0;
- fake_PASS_without_evidence = 0.

## 4. Business/product indicators for later

- time_to_create_new_profession;
- time_to_add_new_skill;
- training cost per verified skill;
- evaluation cost per verified skill;
- regression rate of previously mastered skills;
- percentage of reusable curricula/procedures;
- human expert review time;
- number of professions supported.

No commercial target is approved yet.

## 5. Product Gate interpretation

Product success can be measured without choosing architecture. Exact metric thresholds beyond prototype targets remain subject to validation.
