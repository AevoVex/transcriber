# UI Style — Nordic Utility

Интерфейс настольного приложения в стиле современных developer/system tools: **DevToys + Microsoft PowerToys + Fluent**, выполненный в холодной цветовой палитре **Nord**.

## Общий характер

Минималистичный, функциональный и плотный desktop UI без лишней декоративности.

Основные принципы:

- тёмная холодная цветовая схема;
- чёткое разделение интерфейса на sidebar, toolbar, рабочие панели и карточки;
- небольшие скругления;
- тонкие границы вместо выраженных теней;
- компактные контролы;
- высокая информационная плотность;
- спокойные акцентные цвета;
- большие рабочие области;
- визуальная иерархия строится прежде всего на **разнице оттенков поверхностей**, а не на тенях.

Интерфейс должен ощущаться как **нативная профессиональная desktop-утилита**, а не как web dashboard.

---

## Цветовая палитра — Nord

### Polar Night

Основные тёмные поверхности:

- `#2E3440` — основной фон приложения
- `#3B4252` — sidebar / панели второго уровня
- `#434C5E` — карточки, поля, hover-состояния
- `#4C566A` — borders, separators, disabled elements

### Snow Storm

Текст:

- `#D8DEE9` — основной текст
- `#E5E9F0` — заголовки
- `#ECEFF4` — наиболее контрастный текст и активные элементы

### Frost

Основные акценты:

- `#8FBCBB` — secondary accent
- `#88C0D0` — основной UI accent
- `#81A1C1` — selected / pressed
- `#5E81AC` — глубокий акцент

Главный интерактивный цвет — `#88C0D0`.

Он используется умеренно: active navigation indicator, switches, selected controls, focus borders, progress indicators и важные действия.

### Aurora

Семантические состояния:

- `#BF616A` — error / destructive
- `#D08770` — warning secondary
- `#EBCB8B` — warning
- `#A3BE8C` — success
- `#B48EAD` — дополнительный special/AI accent

---

## Поверхности

Не использовать один сплошной тёмный фон.

Структура строится слоями:

**App background**
`#2E3440`

**Sidebar**
`#292E39` или затемнённый `#2E3440`

**Primary panel**
`#3B4252`

**Cards / inputs / editor surfaces**
`#343B49` – `#434C5E`

**Hover**
`#434C5E`

**Selected**
смесь `#434C5E` с лёгким Frost-акцентом.

Поверхности отличаются друг от друга примерно на 5–12% яркости.

Тени почти отсутствуют.

Для отделения элементов предпочтительнее:

`1px solid rgba(216, 222, 233, 0.08–0.12)`

---

## Sidebar

Левая постоянная навигационная панель шириной примерно **220–260 px**.

Структура:

- логотип и название приложения;
- Search;
- All Tools / Home;
- категории;
- раскрывающиеся группы;
- инструменты внутри групп;
- Settings в нижней части.

Navigation item:

- высота `36–40 px`;
- горизонтальный padding `10–12 px`;
- icon `16–18 px`;
- gap icon/text `8–10 px`;
- radius `4–6 px`.

Hover:

лёгкое осветление поверхности.

Active:

- более светлая Nordic surface;
- слева вертикальный Frost indicator `2–3 px`;
- текст становится `#ECEFF4`;
- icon получает `#88C0D0`.

Не делать активный пункт ярко-синим целиком.

---

## Карточки инструментов

На странице All Tools используется адаптивная сетка карточек.

Карточка:

- background `#3B4252`;
- border `1px`;
- radius `6–8 px`;
- padding `14–18 px`;
- минимальная тень либо полное её отсутствие.

Верхняя часть может содержать квадратную icon surface:

- размер около `56–64 px`;
- background `#434C5E`;
- radius `6 px`;
- monochrome icon `#ECEFF4`.

Ниже:

**Tool Name**

короткое описание muted-цветом.

Внизу могут появляться secondary actions:

favorite, pin, shortcut, open separately.

Hover карточки:

- border становится немного светлее;
- background слегка поднимается по яркости;
- возможно появление action icons.

Не использовать сильное масштабирование карточки при hover.

---

## Панели настроек

Настройки инструмента оформляются горизонтальными плашками, как в DevToys.

Каждая строка:

`[ icon ] [ Label + description ]                         [ control ]`

Например:

`↔  Conversion`  
`   Select conversion mode                     YAML → JSON`

Высота примерно `48–56 px`.

Background немного отличается от основной рабочей поверхности.

Между строками `6–8 px`.

Radius `4–6 px`.

Это позволяет визуально группировать настройки без большого количества рамок и контейнеров.

---

## Рабочая область

Для инструментов типа converter/editor используется двухпанельная компоновка:

`Input | Output`

Панели занимают максимум доступной площади.

Каждая содержит:

- небольшой header;
- название;
- contextual actions справа;
- editor/content area.

Например:

`Input                         Paste  Open  Clear`

и

`Output                              Expand  Copy`

Разделитель между панелями должен быть тонким и допускает drag-resize.

Editor:

- тёмная поверхность;
- line numbers;
- monospace font;
- минимальное количество визуального шума;
- текущая строка может слегка подсвечиваться.

---

## Buttons

### Primary

Использовать редко.

- background `#88C0D0`;
- text `#2E3440`;
- hover `#8FBCBB`;
- radius `5–6 px`.

### Secondary

Основной тип кнопок интерфейса:

- background `#434C5E`;
- text `#E5E9F0`;
- subtle border.

Hover → `#4C566A`.

### Ghost

Для Copy, Clear, Paste, Pin и аналогичных действий:

- прозрачный background;
- icon/text muted;
- background появляется при hover.

---

## Inputs

Search, text input, dropdown и numeric controls:

- высота `32–36 px`;
- background `#3B4252` или `#434C5E`;
- border `1px solid rgba(216,222,233,.10)`;
- radius `4–6 px`.

Focus:

`border-color: #88C0D0`

Допустимо очень слабое внешнее Frost glow, но без яркого neon-эффекта.

Placeholder:

`rgba(216,222,233,.45)`

---

## Dropdown

Dropdown должен выглядеть частью desktop UI, а не браузерным HTML select.

Закрытое состояние:

`YAML to JSON  ˅`

Открытое меню:

- Nordic dark surface;
- тонкая border;
- radius `6 px`;
- selected option имеет Frost indicator или лёгкий Frost tint.

---

## Switches

Компактные Fluent-подобные переключатели.

OFF:

- track `#4C566A`;
- thumb `#D8DEE9`.

ON:

- track `#88C0D0`;
- thumb `#2E3440` или `#ECEFF4`.

Без glow.

---

## Typography

Основной UI font:

**Inter**, **Segoe UI Variable** или системный sans-serif.

Иерархия:

- Page title: `20–24 px`, Semibold
- Section title: `15–17 px`, Semibold
- Control title: `13–14 px`, Medium/Semibold
- Body: `12–14 px`
- Secondary description: `11–12 px`
- Toolbar labels: `11–12 px`

Для кода:

**JetBrains Mono**, **Cascadia Code** или аналогичный monospace.

Не использовать слишком жирный текст.

---

## Icons

Иконки преимущественно outline.

Стиль близкий к:

- Fluent Icons;
- Lucide;
- Phosphor regular.

Обычный размер `16–20 px`.

Большие tool icons — `28–36 px`.

Большинство иконок нейтральные Snow Storm; Frost используется для active/selected состояния.

Не делать каждую категорию разноцветной.

---

## Geometry

Основная геометрия:

- radius small: `4 px`
- radius controls: `5–6 px`
- radius cards: `6–8 px`
- radius modal: `8–10 px`

Не использовать огромные современные web-скругления `16–24 px`.

Spacing строится преимущественно по сетке:

`4 / 8 / 12 / 16 / 24 / 32 px`

---

## Interaction

Анимации короткие:

`100–180 ms`

Использовать:

- background transition;
- border transition;
- opacity;
- небольшое появление contextual actions.

Избегать:

- bounce;
- сильного scale;
- длинных easing-анимаций;
- glassmorphism;
- постоянного glow;
- gradients ради декоративности.

---

## Итоговое визуальное направление

**PowerToys по структуре + DevToys по организации инструментов + Nord по цветам.**

Интерфейс должен выглядеть как единая desktop-платформа с набором инструментов:

- плотный;
- технологичный;
- холодный;
- спокойный;
- современный;
- профессиональный;
- хорошо читаемый;
- без ощущения Electron/web-dashboard шаблона.

Главная визуальная формула:

**Polar Night surfaces + Snow Storm typography + restrained Frost accents + Aurora only for semantic states.**