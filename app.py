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

st.subheader("✏️ Редактирование JSON")
st.caption(
    "Вы можете вручную исправить данные в текстовом поле ниже. "
    "После изменений нажмите «Применить и перерисовать таблицу»."
)

json_text = st.text_area(
    "JSON-данные",
    value=st.session_state.json_text,
    height=400,
    key="json_editor",
    help="Редактируйте JSON напрямую. Убедитесь, что это валидный массив объектов.",
)

col_apply, col_reset = st.columns([3, 1])
with col_apply:
    if st.button("🔄 Применить и перерисовать таблицу", type="primary", use_container_width=True):
        data_new, err = load_json_from_text(json_text)
        if err:
            st.error(err)
        else:
            ok, msg, columns_new, count_new = validate_json(data_new)
            if ok:
                st.session_state.json_data = data_new
                st.session_state.json_text = json_text
                st.session_state.validation_msg = msg
                st.session_state.columns = columns_new
                st.session_state.row_count = count_new
                st.success(f"✅ Данные обновлены: {count_new} строк")
                st.rerun()
            else:
                st.error(msg)
with col_reset:
    if st.button("↩️ Сбросить к исходному", use_container_width=True):
        st.session_state.json_text = json.dumps(
            st.session_state.json_data, ensure_ascii=False, indent=2
        )
        st.rerun()

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
st.markdown(
    """
    <style>
    /* Уменьшаем шрифт и отступы ячеек таблицы */
    div[data-testid="stDataFrame"] table {
        font-size: 11px !important;
        width: 100% !important;
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
    /* Уменьшаем высоту строк */
    div[data-testid="stDataFrame"] div[role="row"] {
        min-height: unset !important;
        height: auto !important;
    }
    /* Сама оболочка таблицы без внутренних скроллов — растягивается по содержимому */
    div[data-testid="stDataFrame"] {
        overflow: visible !important;
    }
    /* Немного убираем лишние отступы у заголовка раздела */
    h2, .stSubheader {
        margin-top: 4px !important;
        margin-bottom: 4px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.info(f"Показано строк: {len(filtered_df):,} из {total_rows:,}")


st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        col: st.column_config.NumberColumn(col) if col_types.get(col) == "numeric" else st.column_config.TextColumn(col)
        for col in filtered_df.columns
    },
)

if "Тип НП" in columns:
    st.caption("💡 Строки с заполненным «Тип НП» (Г./Д.) — группы поселений, без типа — подчинённые записи.")

st.divider()
st.caption("JSON Table Viewer — Streamlit версия. Редактируйте JSON в текстовом поле и нажимайте «Применить» для обновления таблицы.")
