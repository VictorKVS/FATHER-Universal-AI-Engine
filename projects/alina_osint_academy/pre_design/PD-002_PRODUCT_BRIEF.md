# PD-002 · PRODUCT BRIEF

**Project ID:** FATHER-ACADEMY-OSINT-001  
**Product:** ALINA OSINT ACADEMY v0.1  
**Stage:** PRODUCT MANAGER DISCOVERY  
**Status:** DRAFT  
**Architecture:** NOT STARTED  
**Security:** TBD_BY_SECURITY  
**DevSecOps Security:** TBD  
**Legal/Compliance:** TBD_BY_SECURITY_AND_COMPLIANCE

## 1. Product statement

Создать внутри FATHER универсальный механизм профессиональной подготовки интеллектуальных агентов, в котором Алина формирует программу обучения, подбирает первоисточники, выдаёт практические задания, оценивает результаты и подтверждает навыки доказательствами.

Первый профиль — **OSINT Specialist**.

## 2. Problem

Сегодня агент может иметь prompt, RAG, инструменты и интерфейс, но это не доказывает профессиональную компетентность.

Основная проблема:

\`\`\`text
ЗНАНИЯ / PROMPT / TOOLS
        ≠
ПОДТВЕРЖДЁННАЯ ПРОФЕССИОНАЛЬНАЯ КОМПЕТЕНТНОСТЬ
\`\`\`

Нужен управляемый механизм:

\`\`\`text
ПРОФЕССИЯ
 → КОМПЕТЕНЦИИ
 → ЗНАНИЯ
 → ПРАКТИКА
 → ДОКАЗАТЕЛЬСТВА
 → ПРОВЕРКА
 → КОРРЕКЦИЯ
 → ПОВТОР
 → ПОДТВЕРЖДЁННЫЙ НАВЫК
\`\`\`

## 3. Primary users

### Primary
- владелец/оператор FATHER;
- разработчик профессионального агента;
- методист/аналитик, формирующий профессию и критерии навыков.

### Direct runtime participants
- ALINA — преподаватель/методист/экзаменатор;
- обучаемый агент — первый ученик \`ALINA_OSINT_STUDENT\`.

## 4. Customer hypothesis

Для прототипа:

\`\`\`text
CUSTOMER = FATHER PLATFORM OWNER / AGENT FACTORY OPERATOR
USER = AGENT DEVELOPER / METHODIST
LEARNER = PROFESSIONAL AGENT
\`\`\`

Коммерческая модель пока не определяется.

## 5. First narrow use case

**Обучить одного OSINT-агента одному проверяемому профессиональному циклу.**

Первый полигон: \`OSINT-TG-001\`.

Минимальный цикл:

\`\`\`text
ALINA создаёт учебное задание
 → ученик получает задание
 → формирует план
 → использует разрешённые инструменты
 → собирает материалы
 → сохраняет provenance
 → формирует результат
 → evaluator проверяет
 → ошибки фиксируются
 → ученик повторяет
 → SkillProfile изменяется только по доказательствам
\`\`\`

## 6. Value proposition

### Для FATHER
- стандартизированный механизм выращивания специалистов;
- повторно используемая схема для разных профессий;
- доказуемая компетентность вместо декларативной;
- история обучения и ошибок;
- управляемые уровни самостоятельности.

### Для разработчика агента
- понятно, чему агент уже обучен;
- видно, что он реально умеет;
- видно, какие навыки не подтверждены;
- можно повторять обучение и сравнивать версии.

## 7. MVP value hypothesis

Если FATHER сможет провести один полный учебный цикл OSINT-агента от задания до повторного экзамена и доказуемого изменения SkillProfile, значит механизм пригоден как основа общей фабрики профессиональных агентов.

## 8. Product principles

- NO EVIDENCE → NO MASTERY.
- RAG ≠ COMPETENCE.
- UI ≠ WORKING SYSTEM.
- KNOWLEDGE CONFIDENCE ≠ STUDENT MASTERY.
- SOURCE TRACEABILITY IS MANDATORY.
- HUMAN APPROVAL FOR HIGH-RISK ACTIONS.
- BEHAVIOR/PROCEDURE TRAINING FIRST.
- MODEL WEIGHT TRAINING LATER.
- REUSE EXISTING FATHER/OSINT COMPONENTS WHERE PROVEN.

## 9. MVP scope

IN:
- 1 преподаватель — ALINA;
- 1 ученик — OSINT-агент;
- 1 профессия;
- 1 curriculum;
- 1 knowledge/competency graph;
- 1 training assignment;
- 1 evidence flow;
- 1 evaluator;
- 1 SkillProfile;
- 1 повторный цикл;
- 1 отчёт обучения.

OUT:
- полноценный LMS;
- десятки профессий;
- SFT/DPO/RL;
- автономный доступ ко всем OSINT-инструментам;
- производственная сертификация агента;
- отдельная образовательная платформа;
- коммерческая модель;
- архитектурное решение на этапе PM.

## 10. Success at product level

Прототип ценен, если он доказывает:

1. программа обучения сохраняется;
2. задание воспроизводимо;
3. источники прослеживаются;
4. evaluator выявляет ошибки;
5. ошибки влияют на повторное обучение;
6. SkillProfile меняется только после проверки;
7. состояние восстанавливается после повторного запуска;
8. один и тот же механизм можно потенциально применить к другой профессии без полной переделки.

## 11. Dependencies

- существующий FATHER Analytical Core;
- ALINA;
- OSINT_deepseek как первый полигон;
- существующие collector/evidence/evaluation компоненты — после инвентаризации и подтверждения пригодности.

## 12. Product risks

- подмена обучения накоплением RAG;
- слишком широкий scope профессии OSINT;
- ложное чувство компетентности;
- невозможность объективно измерить отдельные навыки;
- сильная связность с одним конкретным OSINT-проектом;
- неустойчивые внешние источники;
- чрезмерная стоимость evaluation;
- высокая сложность построения универсальной модели компетенций.

## 13. Security placeholders

\`\`\`text
SECURITY_STATUS: TBD_BY_SECURITY
DEVSECOPS_SECURITY_STATUS: TBD
MANDATORY_CONTROLS: TBD_BY_SECURITY
MANDATORY_LICENSES: TBD_BY_SECURITY
SECURITY_COST: TBD_BY_SECURITY
DEVSECOPS_COST: TBD_BY_SECURITY_AND_DEVSECOPS
\`\`\`

## 14. Product decision

**Proceed to complete Product Manager Pack.**

No architecture approval is granted by this document.
