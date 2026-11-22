import json
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="JSON Table Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def validate_json(data: Any) -> Tuple[bool, str, Optional[List[str]], Optional[int]]:
    if data is None:
        return False, "JSON пуст или не содержит данных.", None, None
    if not isinstance(data, list):
        return False, "Корневой элемент должен быть массивом (списком) объектов.", None, None
    if len(data) == 0:
        return False, "Массив пуст — нечего отображать.", None, None
    non_dict = [i for i, item in enumerate(data) if not isinstance(item, dict)]
    if non_dict:
        idx_str = ", ".join(str(i) for i in non_dict[:10])
        return (
            False,
            f"Элементы с индексами [{idx_str}] не являются объектами (dict). Все элементы должны быть объектами.",
            None,
            None,
        )
    columns = list(data[0].keys())
    inconsistent = []
    for i, item in enumerate(data):
        if list(item.keys()) != columns:
            inconsistent.append(i)
            if len(inconsistent) >= 10:
                break
    if inconsistent:
        idx_str = ", ".join(str(i) for i in inconsistent)
        return (
            False,
            f"Объекты с индексами [{idx_str}] имеют разный набор ключей. Все объекты должны иметь одинаковые столбцы.",
            None,
            None,
        )
    return True, "OK", columns, len(data)


def load_json_from_text(text: str) -> Tuple[Optional[Any], str]:
    try:
        data = json.loads(text)
        return data, ""
    except json.JSONDecodeError as e:
        return None, f"Ошибка парсинга JSON: {e.msg} (позиция {e.pos})"


def get_column_types(df: pd.DataFrame) -> Dict[str, str]:
    types = {}
    for col in df.columns:
        non_null = df[col].dropna()
        non_null = non_null[non_null != ""]
        if len(non_null) == 0:
            types[col] = "text"
            continue
        try:
            pd.to_numeric(non_null)
            types[col] = "numeric"
        except (ValueError, TypeError):
            types[col] = "text"
    return types


import html

def format_json_html(obj, indent=0):
    """Рекурсивно форматирует JSON-объект в HTML с подсветкой синтаксиса."""
    spaces = "  " * indent
    next_spaces = "  " * (indent + 1)

    if obj is None:
        return f'{spaces}<span class="json-null">null</span>'
    elif isinstance(obj, bool):
        return f'{spaces}<span class="json-bool">{str(obj).lower()}</span>'
    elif isinstance(obj, (int, float)):
        return f'{spaces}<span class="json-number">{obj}</span>'
    elif isinstance(obj, str):
        escaped = html.escape(obj, quote=True)
        return f'{spaces}<span class="json-string">"{escaped}"</span>'
    elif isinstance(obj, list):
        if not obj:
            return f'{spaces}<span class="json-punct">[]</span>'
        items = []
        for i, item in enumerate(obj):
            comma = ',' if i < len(obj) - 1 else ''
            items.append(f'{next_spaces}{format_json_html(item, indent + 1)}<span class="json-punct">{comma}</span>')
        inner = '\n'.join(items)
        return f'{spaces}<span class="json-punct">[</span>\n{inner}\n{spaces}<span class="json-punct">]</span>'
    elif isinstance(obj, dict):
        if not obj:
            return f'{spaces}<span class="json-punct">{{}}</span>'
        items = []
        keys = list(obj.keys())
        for i, key in enumerate(keys):
            comma = ',' if i < len(keys) - 1 else ''
            escaped_key = html.escape(key, quote=True)
            items.append(
                f'{next_spaces}<span class="json-key">"{escaped_key}"</span>'
                f'<span class="json-punct">:</span> {format_json_html(obj[key], indent + 1)}'
                f'<span class="json-punct">{comma}</span>'
            )
        inner = '\n'.join(items)
        return f'{spaces}<span class="json-punct">{{</span>\n{inner}\n{spaces}<span class="json-punct">}}</span>'
    else:
        return f'{spaces}{html.escape(str(obj))}'


if "json_data" not in st.session_state:
    st.session_state.json_data = None
if "json_text" not in st.session_state:
    st.session_state.json_text = ""
if "validation_msg" not in st.session_state:
    st.session_state.validation_msg = ""
if "columns" not in st.session_state:
    st.session_state.columns = None
if "row_count" not in st.session_state:
    st.session_state.row_count = 0


st.title("📊 JSON Table Viewer")
st.caption("Просмотр, валидация и ручное редактирование единообразных JSON-данных в виде таблицы")

with st.sidebar:
    st.header("📁 Загрузка JSON")

    uploaded = st.file_uploader(
        "Выберите JSON-файл",
        type=["json"],
        accept_multiple_files=False,
        help="Файл должен содержать массив объектов с одинаковыми ключами",
    )

    if uploaded is not None:
        file_bytes = uploaded.read()
        try:
            file_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                file_text = file_bytes.decode("cp1251")
            except UnicodeDecodeError:
                file_text = file_bytes.decode("latin-1")

        st.session_state.json_text = file_text
        data, err = load_json_from_text(file_text)

        if err:
            st.session_state.json_data = None
            st.session_state.validation_msg = err
            st.session_state.columns = None
            st.session_state.row_count = 0
            st.error(err)
        else:
            ok, msg, columns, count = validate_json(data)
            st.session_state.json_data = data
            st.session_state.validation_msg = msg
            st.session_state.columns = columns
            st.session_state.row_count = count if count else 0

            if ok:
                st.success(f"✅ Загружено строк: {count}")
                st.info(f"Столбцы: {', '.join(columns)}")
            else:
                st.error(msg)

    st.divider()

    if st.button("📋 Загрузить пример данных", use_container_width=True):
        example = [
            {
                "Номер ревизии": 5,
                "Уезд": "Бугурусланский",
                "Тип НП": "Г.",
                "Населенный пункт": "Бугуруслан",
                "Сословные и конфессиональные группы": "Причисленные по указу Уфимской казенной палаты",
                "ДМП": 9,
                "ДЖП": 8,
            },
            {
                "Номер ревизии": 5,
                "Уезд": "Бугурусланский",
                "Тип НП": "",
                "Населенный пункт": "Нижней Ермаковой",
                "Сословные и конфессиональные группы": "Служилые татары",
                "ДМП": 64,
                "ДЖП": 48,
            },
            {
                "Номер ревизии": 6,
                "Уезд": "Бугурусланский",
                "Тип НП": "Д.",
                "Населенный пункт": "Надырово (Балыклы куль)",
                "Сословные и конфессиональные группы": "Ясашные татары",
                "ДМП": 51,
                "ДЖП": None,
            },
        ]
        text = json.dumps(example, ensure_ascii=False, indent=2)
        st.session_state.json_text = text
        data, err = load_json_from_text(text)
        if err:
            st.error(err)
        else:
            ok, msg, columns, count = validate_json(data)
            st.session_state.json_data = data
            st.session_state.validation_msg = msg
            st.session_state.columns = columns
            st.session_state.row_count = count if count else 0
            if ok:
                st.success(f"✅ Пример загружен: {count} строк")
            else:
                st.error(msg)

    st.divider()

    if st.session_state.json_text:
        st.download_button(
            label="⬇️ Скачать JSON",
            data=st.session_state.json_text.encode("utf-8"),
            file_name="edited.json",
            mime="application/json",
            use_container_width=True,
        )

if st.session_state.json_data is None:
    st.info("Загрузите JSON-файл или нажмите «Загрузить пример данных» в боковой панели.")
    st.stop()

data: List[Dict] = st.session_state.json_data
columns: List[str] = st.session_state.columns
row_count: int = st.session_state.row_count

st.subheader("📈 Статистика")
col1, col2, col3, col4 = st.columns(4)

total_rows = len(data)
col1.metric("Всего строк", f"{total_rows:,}")

dmp_sum = 0
dzhp_sum = 0
dmp_count = 0
dzhp_count = 0
for row in data:
    dmp = row.get("ДМП")
    if isinstance(dmp, (int, float)):
        dmp_sum += dmp
        dmp_count += 1
    dzhp = row.get("ДЖП")
    if isinstance(dzhp, (int, float)):
        dzhp_sum += dzhp
        dzhp_count += 1

col2.metric("Сумма ДМП", f"{dmp_sum:g}" if dmp_count > 0 else "—")
col3.metric("Сумма ДЖП", f"{dzhp_sum:g}" if dzhp_count > 0 else "—")
col4.metric("Столбцов", len(columns))

if st.session_state.validation_msg and st.session_state.validation_msg != "OK":
    st.warning(f"⚠️ {st.session_state.validation_msg}")

import streamlit.components.v1 as components

st.subheader("📄 Исходный JSON")

html_json = format_json_html(st.session_state.json_data)

components.html(
    f"""
    <style>
    .json-key {{ color: #1a73e8 !important; font-weight: 600 !important; }}
    .json-string {{ color: #0b8043 !important; }}
    .json-number {{ color: #d97706 !important; }}
    .json-bool {{ color: #6d28d9 !important; }}
    .json-null {{ color: #6d28d9 !important; }}
    .json-punct {{ color: #666666 !important; }}
    </style>
    <div style="background-color: #f8f9fa; border: 1px solid #e6e6e6; border-radius: 4px; padding: 8px; font-family: 'Consolas', 'Monaco', monospace; font-size: 11px; line-height: 1.3; white-space: pre-wrap; word-wrap: break-word; overflow: visible; max-height: none; height: auto;">
        <pre>{html_json}</pre>
    </div>
    """,
    height=600,
    scrolling=True,
)

st.divider()
st.subheader("📋 Таблица")

df = pd.DataFrame(data, columns=columns)
col_types = get_column_types(df)

# Поиск и фильтры (применяются одновременно)
col_f1, col_f2, col_f3 = st.columns([1, 1, 2])

rev_values = []
uezd_values = []
if "Номер ревизии" in df.columns:
    rev_values = sorted(df["Номер ревизии"].dropna().unique().tolist())
if "Уезд" in df.columns:
    uezd_values = sorted(df["Уезд"].dropna().unique().tolist())

with col_f1:
    selected_rev = st.multiselect(
        "Номер ревизии",
        options=rev_values,
        default=[],
        key="filter_revision",
        help="Выберите один или несколько номеров ревизии",
    )

with col_f2:
    selected_uezd = st.multiselect(
        "Уезд",
        options=uezd_values,
        default=[],
        key="filter_uezd",
        help="Выберите один или несколько уездов",
    )

with col_f3:
    search_term = st.text_input(
        "🔍 Поиск по всем столбцам",
        value="",
        key="search_input",
    )

filtered_df = df.copy()

if selected_rev and "Номер ревизии" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Номер ревизии"].isin(selected_rev)]

if selected_uezd and "Уезд" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Уезд"].isin(selected_uezd)]

if search_term:
    mask = pd.Series(False, index=filtered_df.index)
    for col in filtered_df.columns:
        col_mask = filtered_df[col].astype(str).str.contains(search_term, case=False, na=False)
        mask = mask | col_mask
    filtered_df = filtered_df[mask]

# Компактные стили таблицы: меньше отступы и шрифт, чтобы вместить больше строк на экран
# (сортировка, фильтрация и изменение ширины мышкой работают через st.dataframe)
st.markdown(
    """
    <style>
    h2, .stSubheader {
        margin-top: 4px !important;
        margin-bottom: 4px !important;
    }
    /* Компактный шрифт и отступы ячеек */
    div[data-testid="stDataFrame"] table {
        font-size: 11px !important;
        border-collapse: collapse !important;
        table-layout: fixed !important;
    }
    div[data-testid="stDataFrame"] th,
    div[data-testid="stDataFrame"] td {
        padding: 2px 4px !important;
        font-size: 11px !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    div[data-testid="stDataFrame"] th {
        background-color: #f0f2f6 !important;
        font-weight: 600 !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
    }
    div[data-testid="stDataFrame"] tr:nth-child(even) td {
        background-color: #fafafa !important;
    }
    /* Строго 50px для выбранных колонок (по порядку: 1, 3, 6, 7) */
    div[data-testid="stDataFrame"] th:nth-child(1),
    div[data-testid="stDataFrame"] td:nth-child(1),
    div[data-testid="stDataFrame"] th:nth-child(3),
    div[data-testid="stDataFrame"] td:nth-child(3),
    div[data-testid="stDataFrame"] th:nth-child(6),
    div[data-testid="stDataFrame"] td:nth-child(6),
    div[data-testid="stDataFrame"] th:nth-child(7),
    div[data-testid="stDataFrame"] td:nth-child(7) {
        width: 50px !important;
        max-width: 50px !important;
        min-width: 50px !important;
    }
    /* Таблица не растягивается на всю ширину — только по содержимому */
    div[data-testid="stDataFrame"] {
        max-width: none !important;
        width: -moz-fit-content !important;
        width: fit-content !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.info(f"Показано строк: {len(filtered_df):,} из {total_rows:,}")

# Ширина колонок: 50 px для Номер ревизии, Тип НП, ДМП, ДЖП
column_config = {}
for col in filtered_df.columns:
    if col in ("Номер ревизии", "Тип НП", "ДМП", "ДЖП"):
        if col_types.get(col) == "numeric":
            column_config[col] = st.column_config.NumberColumn(col, width=50)
        else:
            column_config[col] = st.column_config.TextColumn(col, width=50)
    elif col_types.get(col) == "numeric":
        column_config[col] = st.column_config.NumberColumn(col)
    else:
        column_config[col] = st.column_config.TextColumn(col)

st.dataframe(
    filtered_df,
    hide_index=True,
    column_config=column_config,
)

if "Тип НП" in columns:
    st.caption("💡 Строки с заполненным «Тип НП» (Г./Д.) — группы поселений, без типа — подчинённые записи.")

st.divider()
st.caption("JSON Table Viewer — Streamlit версия.")
