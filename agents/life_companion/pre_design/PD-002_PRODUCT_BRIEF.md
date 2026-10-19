# PD-002 · PRODUCT BRIEF

**Project ID:** LIFE-001  
**Agent ID:** FATHER-LIFE-COMPANION-001  
**Document ID:** PD-002  
**Stage:** PRODUCT MANAGER DISCOVERY  
**Status:** DRAFT  
**Version:** 0.1  
**Architecture:** NOT STARTED  
**Security:** NOT ASSESSED — next mandatory stage after Product Pack  
**Owner:** Product Manager  
**Next owner:** Product Manager → PD-003/004/005/006, then Information Security Intake

---

# 1. Product idea

Создать персональную цифровую систему, которая сопровождает одного человека на протяжении жизни, сохраняет непрерывность полезного контекста и помогает организовывать информацию, задачи и решения в зависимости от жизненного этапа человека.

Ключевая идея продукта — не "вечный чат-бот", а сохранение жизненного контекста и управляемая передача его между этапами жизни, устройствами, сервисами, специалистами и доверенными лицами.

---

# 2. Problem statement

Сегодня важная информация о жизни человека фрагментирована:

- документы находятся в разных местах;
- решения и причины решений забываются;
- сроки и обязательства распределены по разным системам;
- история здоровья, обучения, работы, имущества, договоров и взаимодействия с организациями живёт в разных источниках;
- при обращении к врачу, юристу, работодателю, банку, государственному органу или другому специалисту человеку приходится заново собирать контекст;
- при смене устройства, сервиса или поставщика часть истории теряется;
- семья часто не понимает, где находятся важные документы и какие решения были заранее приняты;
- с возрастом объём накопленного контекста становится слишком большим для ручного управления.

## Product problem

~~~text
ЧЕЛОВЕК ЖИВЁТ ДЕСЯТИЛЕТИЯ
        ↓
ИНФОРМАЦИЯ И РЕШЕНИЯ РАСПАДАЮТСЯ ПО СИСТЕМАМ
        ↓
КОНТЕКСТ ТЕРЯЕТСЯ
        ↓
ОДНИ И ТЕ ЖЕ ДАННЫЕ СОБИРАЮТСЯ ЗАНОВО
        ↓
РАСТУТ ОШИБКИ, ПРОПУСКИ И ЗАТРАТЫ ВРЕМЕНИ
~~~

---

# 3. Product vision

Создать персональный слой непрерывности, который позволяет человеку:

- видеть важную историю своей жизни;
- понимать текущее состояние дел;
- быстро находить подтверждающие документы и источники;
- помнить, почему было принято важное решение;
- не терять обязательства и сроки;
- готовить контекст для взаимодействия со специалистами;
- переносить накопленный контекст между технологиями и жизненными этапами;
- сохранять контроль над тем, кому и что разрешено видеть или делать.

---

# 4. Primary user

## Initial user hypothesis

Первый целевой пользователь — самостоятельный совершеннолетний человек, который:

- ведёт несколько параллельных жизненных контуров;
- хранит значимый объём документов и цифровой информации;
- регулярно взаимодействует с организациями и специалистами;
- имеет задачи, обязательства и долгосрочные решения;
- заинтересован в сохранении личной истории и контекста.

Это стартовая гипотеза.

Детский, опекунский, пожилой и end-of-life режимы остаются частью долгосрочной идеи, но **не являются первым MVP**.

---

# 5. Customer hypothesis

На первом этапе:

~~~text
USER = CUSTOMER = OWNER OF PERSONAL CONTEXT
~~~

Позже возможны другие модели:

- семейная подписка;
- корпоративный benefit;
- страховой/медицинский/банковский/государственный канал;
- care ecosystem;
- white-label platform.

Эти модели НЕ включены в первый продуктовый scope.

---

# 6. First narrow use case

## LIFE CONTINUITY DESK

Первая версия должна доказать одну гипотезу:

> человек получает измеримую ценность от единого управляемого слоя личного контекста, который связывает документы, события, обязательства, решения и подтверждающие источники.

### First slice

Пользователь может:

1. добавить или подключить важную информацию;
2. разложить её по жизненным объектам и событиям;
3. увидеть хронологию;
4. связать документ с событием/решением/обязательством;
5. зафиксировать важное решение и причину;
6. получить напоминание о сроке/обязательстве;
7. собрать пакет контекста для человека-специалиста;
8. экспортировать собственный контекст в переносимом виде.

### Example

~~~text
"Мне через месяц продлевать договор/страховку/документ"

Система показывает:
- какой объект;
- исходный документ;
- срок;
- предыдущие действия;
- связанные контакты;
- что нужно подготовить;
- что неизвестно;
- откуда получена информация.
~~~

---

# 7. Value proposition

## Functional value

Сократить потери контекста и время на повторный сбор информации.

## Emotional value

Дать человеку ощущение управляемости собственной цифровой жизни без передачи агенту права принимать жизнь за него.

## Long-term value

Создать переносимую личную историю, не привязанную навечно к одному интерфейсу, модели или поставщику.

---

# 8. Product principles

### PP-001 Human remains principal

~~~text
AGENT ASSISTS
HUMAN DECIDES
~~~

### PP-002 Continuity over chat

Ценность продукта определяется не качеством одного диалога, а сохранением и полезным использованием контекста во времени.

### PP-003 Source-aware information

Важная информация должна иметь происхождение: документ, человек, система, событие, запись или иное основание.

### PP-004 Facts ≠ interpretations ≠ recommendations

Продукт должен различать:

- известный факт;
- утверждение пользователя;
- извлечённое значение;
- вывод;
- рекомендацию;
- предпочтение;
- неизвестность.

### PP-005 Portability

Личный контекст не должен быть логически привязан к одной LLM, одному облаку или одному пользовательскому интерфейсу.

### PP-006 Progressive expansion

Высокорисковые области не включаются только потому, что технически их можно подключить.

---

# 9. Desired outcome

Пользователь должен быстрее отвечать на вопросы:

~~~text
Что у меня происходит?
Что требует внимания?
Что я уже делал по этому вопросу?
Почему я принял это решение?
Какие документы это подтверждают?
Что нужно сделать дальше?
Что мне передать специалисту?
Чего система НЕ знает?
~~~

---

# 10. MVP scope

### IN SCOPE

- пользовательский профиль;
- личные объекты/дела;
- документы и ссылки на источники;
- события и временная линия;
- задачи/сроки/обязательства;
- решения и причины решений;
- связи между объектами;
- поиск и структурированное представление;
- формирование human-readable context package;
- импорт/экспорт собственного контекста;
- явная маркировка неизвестного/неподтверждённого.

### OUT OF SCOPE FOR MVP

- автономные медицинские решения;
- автономные юридические решения;
- автономные финансовые операции;
- покупки без подтверждения;
- подписание документов;
- управление банковскими счетами;
- контроль ребёнка/опека;
- биометрический контроль;
- скрытая слежка;
- social scoring;
- автоматическая передача данных третьим лицам;
- постоянный доступ ко всем сообщениям и устройствам;
- цифровое наследование;
- диагностика здоровья;
- emergency-response automation.

---

# 11. AS-IS

Типичный пользователь использует несколько несвязанных систем:

~~~text
FILES
EMAIL
MESSENGERS
CALENDAR
NOTES
CLOUD STORAGE
BANK
GOV SERVICES
HEALTH APPS
WORK SYSTEMS
PAPER DOCUMENTS
MEMORY
OTHER PEOPLE
~~~

Контекст собирается вручную и ситуативно.

Основные потери:

- забытый срок;
- отсутствующий документ;
- неизвестная актуальная версия;
- забытая причина решения;
- повторный ввод информации;
- невозможность быстро собрать историю вопроса;
- невозможность понять происхождение отдельного утверждения.

---

# 12. TO-BE product-level view

~~~text
PERSON
   ↓
PERSONAL CONTEXT LAYER
   ├── objects
   ├── events
   ├── documents
   ├── obligations
   ├── decisions
   ├── provenance
   └── uncertainty
   ↓
VIEW / SEARCH / REMIND / PACKAGE / EXPORT
   ↓
HUMAN DECISION
~~~

Это продуктовая модель, не архитектурная схема.

---

# 13. Success metrics — draft

## Product metrics

- time_to_find_important_context;
- time_to_prepare_specialist_handoff;
- percent_of_tracked_obligations_with_known_deadline;
- percent_of_important_records_with_source/provenance;
- percent_of_user-critical_context_exportable;
- successful_restore_or_migration_rate;
- number_of_prevented_or_detected_missed_deadlines;
- user-confirmed usefulness of generated context packages.

## Safety / trust indicators

- unauthorized_action_count = 0 target;
- hidden_data_sharing_count = 0 target;
- irrecoverable_context_loss_count = 0 target;
- clearly_unverifiable_claim_rate;
- user_correction_rate;
- provenance_coverage.

Exact target values are TBD and must be calibrated during validation.

---

# 14. Product constraints

- long lifetime of data;
- technologies and vendors will change;
- laws and jurisdictions will change;
- user authority may change over life;
- information sensitivity varies strongly by domain;
- context may contain contradictions;
- some historical data will be wrong;
- some information must be deleted or become inaccessible;
- availability of external systems cannot be assumed;
- the product must remain useful even when individual AI providers are unavailable.

These are product constraints, not technical solutions.

---

# 15. Key assumptions

### A-001
Users value continuity more than another conversational assistant.

### A-002
Users are willing to curate at least part of their important context.

### A-003
Useful automation is possible without unrestricted access to all personal data.

### A-004
The product can preserve provenance and uncertainty in a way understandable to non-technical users.

### A-005
A narrow administrative/continuity MVP can demonstrate value before entering health, finance, legal autonomy or child-care scenarios.

### A-006
Portability is valuable enough to justify being a first-class product requirement.

### A-007
Users will trust the product only if visibility and control are stronger than in ordinary assistants.

All assumptions remain unvalidated.

---

# 16. Product risks — non-security discovery level

- scope explosion caused by "whole life" positioning;
- unclear first willingness-to-pay;
- user fatigue from manual data maintenance;
- excessive complexity;
- low perceived value until enough context accumulates;
- poor source quality;
- outdated information becoming harmful;
- dependence on integrations;
- difficult migration across decades;
- confusing assistant recommendation with professional advice.

Security/legal risks are intentionally deferred to PD-007..PD-014.

---

# 17. First product hypothesis

~~~text
IF

an adult user can keep important
documents + events + obligations + decisions + provenance
in one portable personal context

AND

the system can quickly assemble the relevant context
without taking autonomous high-impact actions

THEN

the user will spend less time rebuilding personal history
and will miss fewer important obligations.
~~~

---

# 18. Validation questions

Before Product Gate:

1. Which real recurring life scenarios produce the highest context-loss cost?
2. Which 3–5 object types are sufficient for MVP?
3. How much manual input will users tolerate?
4. Does timeline + document + obligation + decision provide enough initial value?
5. What information do users refuse to place in such a system?
6. Is portability a purchase driver or merely an engineering preference?
7. How quickly must value appear: first day, week, month?
8. Which context-package scenarios are most valuable?
9. What is the minimum trust model users expect before importing real documents?
10. Which functions require connectivity and which must remain useful offline?

---

# 19. Product decisions at v0.1

### DEC-PD002-001
The broad "birth to death" idea remains long-term vision, not MVP scope.

### DEC-PD002-002
The first target is an independent adult user.

### DEC-PD002-003
The first product slice is LIFE CONTINUITY DESK.

### DEC-PD002-004
MVP proves continuity of context, not autonomous life management.

### DEC-PD002-005
High-risk vertical autonomy is explicitly excluded from MVP.

### DEC-PD002-006
Portability and provenance are product properties from the beginning.

---

# 20. Handoff to next Product Manager artifacts

PD-002 supplies input to:

~~~text
PD-003 STAKEHOLDER_MAP
PD-004 VALUE_AND_SUCCESS_METRICS
PD-005 SCOPE_AND_NON_GOALS
PD-006 ASSUMPTION_REGISTER
~~~

After these four are reviewed:

~~~text
GATE-PD01-PRODUCT
        ↓
PD-007 SECURITY_CONTEXT
        ↓
INFORMATION SECURITY INTAKE
~~~

No Business Analysis or System Analysis should begin before that Security Intake.
