"""Альбом-редактор блок-схем (index.html).

Одностраничное приложение, которому не нужны ни сеть, ни сервер: в файл
кладётся модель каждой схемы (фигуры, линии, подписи), а браузер рисует
её сам тем же алгоритмом, что и Python. Линии при правке прокладывает
libavoid (Adaptagrams) — он встроен в страницу из vendor/web. Это даёт
полноценный редактор:

* перетаскивание блоков и изменение их размеров, линии обходят блоки;
* правка узлов линии, перепривязка концов к другим блокам;
* создание схем с нуля — палитра блоков, инструмент связи, подписи;
* отмена/повтор, копирование, выравнивание по сетке;
* экспорт в SVG (аккуратное дерево слоёв для Figma) и PNG, печать;
* сохранение в браузере и выгрузка всего проекта одним .json-файлом.
"""

import base64
import json

from .text import xml_escape
from .vendored import web_asset

CSS = r"""
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#eef1f5; --panel:#fff; --ink:#111820; --muted:#67757f; --line:#dbe2ea;
  --accent:#2f6fd0; --accent-soft:#e8f0fd; --danger:#c0392b; --hover:#f2f5f9;
  --field:#fbfcfe; --chart-bg:#ffffff;
  --shadow:0 1px 2px rgba(16,24,32,.06),0 6px 20px rgba(16,24,32,.07);
  --font:"Segoe UI","Noto Sans",Inter,Arial,sans-serif;
}
body[data-theme="dark"]{
  --bg:#0d1117; --panel:#161b22; --ink:#e6edf3; --muted:#8b949e; --line:#26303b;
  --accent:#4a90e2; --accent-soft:#1a2b42; --danger:#f2726f; --hover:#1c242e;
  --field:#0f151d; --chart-bg:#11161d;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.35);
  color-scheme:dark;
}
html,body{height:100%}
body{margin:0;font-family:var(--font);background:var(--bg);color:var(--ink);
     font-size:14px;overflow:hidden;-webkit-user-select:none;user-select:none}
button,select,input,textarea{font:inherit;color:inherit}
button{cursor:pointer;background:var(--panel);border:1px solid var(--line);
       border-radius:8px;padding:6px 11px}
button:hover{background:var(--hover);border-color:var(--muted)}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button.primary:hover{background:#265fb8}
button.on{background:var(--accent-soft);border-color:#b7d0f2;color:#1d4f9e}
button.ghost{border-color:transparent;background:transparent}
button:disabled{opacity:.4;cursor:default}
.topbar{height:52px;display:flex;align-items:center;gap:8px;padding:0 14px;
        background:var(--panel);border-bottom:1px solid var(--line);z-index:20}
.brand{font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.brand .sub{color:var(--muted);font-weight:400;font-size:12.5px}
.grow{flex:1 1 auto}.group{display:flex;gap:6px;align-items:center}
.sep{width:1px;height:24px;background:var(--line);margin:0 3px}
.layout{display:flex;height:calc(100vh - 52px)}
aside{background:var(--panel);display:flex;flex-direction:column;min-height:0}
aside.nav{flex:0 0 250px;border-right:1px solid var(--line)}
aside.insp{flex:0 0 280px;border-left:1px solid var(--line);padding:12px 14px;
           overflow:auto}
.navhead{display:flex;gap:6px;padding:10px 10px 6px}
.navhead input{flex:1 1 auto;min-width:0;padding:6px 9px;border:1px solid var(--line);
               border-radius:8px;background:var(--field);color:var(--ink)}
.tree{overflow:auto;padding:0 8px 14px;min-height:0;flex:1 1 auto}
.tree .sec{font-size:11px;letter-spacing:.07em;text-transform:uppercase;
           color:var(--muted);padding:12px 8px 5px;font-weight:600}
.tree a{display:flex;gap:6px;align-items:baseline;padding:6px 9px;border-radius:7px;
        color:var(--ink);text-decoration:none;overflow-wrap:anywhere;line-height:1.35;
        cursor:pointer}
.tree a:hover{background:var(--hover)}
.tree a.active{background:var(--accent-soft);color:#1d4f9e;font-weight:600}
.tree a .ln{color:var(--muted);font-size:11.5px;font-weight:400;margin-left:auto}
.tree a.edited .ln::after{content:" •";color:var(--accent)}
main{flex:1 1 auto;display:flex;flex-direction:column;min-width:0;min-height:0}
.toolbar{height:46px;display:flex;align-items:center;gap:7px;padding:0 12px;
         border-bottom:1px solid var(--line);background:var(--panel)}
.toolbar .name{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.toolbar .meta{color:var(--muted);font-size:12.5px;font-family:Consolas,monospace;
               white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:38%}
.zoomval{min-width:50px;text-align:center;color:var(--muted);font-variant-numeric:tabular-nums}
.work{flex:1 1 auto;display:flex;min-height:0}
.palette{flex:0 0 58px;border-right:1px solid var(--line);background:var(--panel);
         padding:8px 0;display:flex;flex-direction:column;gap:4px;align-items:center;
         overflow:auto}
.palette button{width:42px;height:42px;padding:0;display:grid;place-items:center;
                border-radius:9px}
.palette .gap{height:8px}
.palette svg{pointer-events:none}
.stage{flex:1 1 auto;overflow:auto;padding:22px;min-height:0}
.sheet{background:var(--chart-bg);border-radius:10px;box-shadow:var(--shadow);padding:16px;
       margin:0 auto;width:max-content;max-width:none}
.sheet svg{display:block;touch-action:none}
.caption{text-align:center;color:var(--muted);padding:10px 0 24px;font-size:13px}
.hint{position:absolute;pointer-events:none}
svg .shp{cursor:move}
svg .edge-hit{stroke:transparent;stroke-width:12;fill:none;cursor:pointer}
svg .sel-outline{fill:none;stroke:var(--accent);stroke-width:2;
                 stroke-dasharray:5 3;pointer-events:none}
svg .handle{fill:#fff;stroke:var(--accent);stroke-width:1.6;cursor:pointer}
svg .handle.mid{fill:var(--accent-soft)}
svg .handle.bound{fill:#2f9e44;stroke:#237032}
svg .guide{stroke:#e8590c;stroke-width:1;stroke-dasharray:4 3;pointer-events:none}
svg .marquee{fill:rgba(47,111,208,.10);stroke:var(--accent);stroke-width:1;
             stroke-dasharray:4 3;pointer-events:none}
.insp h3{margin:0 0 6px;font-size:12px;letter-spacing:.05em;text-transform:uppercase;
         color:var(--muted)}
.insp label{display:block;font-size:12.5px;color:var(--muted);margin:12px 0 5px}
.insp select,.insp textarea,.insp input{width:100%;padding:7px 9px;
  border:1px solid var(--line);border-radius:8px;background:var(--field);color:var(--ink)}
.insp textarea{min-height:88px;resize:vertical;font-family:Consolas,monospace;
               font-size:13px;line-height:1.45}
.insp .row{display:flex;gap:6px;margin-top:10px}
.insp .row>*{flex:1 1 auto}
.insp .note{color:var(--muted);font-size:12.2px;line-height:1.55;margin-top:14px}
.insp .kbd{font-family:Consolas,monospace;background:var(--hover);border:1px solid var(--line);
           border-radius:4px;padding:0 4px}
.toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,14px);
       background:#111820;color:#fff;padding:9px 16px;border-radius:9px;font-size:13px;
       opacity:0;pointer-events:none;transition:.2s;z-index:60}
.toast.show{opacity:1;transform:translate(-50%,0)}
/* новые мелочи интерфейса */
.check{display:flex;align-items:center;gap:6px;white-space:nowrap;color:var(--muted);
       font-size:12.5px;padding:0 4px;cursor:pointer}
.check input{width:14px;height:14px;accent-color:var(--accent);cursor:pointer}
button.tiny{padding:3px 7px;font-size:13px;color:var(--muted)}
button.danger{color:var(--danger)}
.navfoot{padding:8px 10px;border-top:1px solid var(--line)}
.navfoot button{width:100%}
.toolbar .name{cursor:text}
.only-narrow{display:none}

@media print{
  body{overflow:visible;background:#fff}
  .topbar,aside,.toolbar,.palette{display:none!important}
  .layout,.work{display:block;height:auto}
  .stage{overflow:visible;padding:0}
  .sheet{box-shadow:none;border-radius:0;padding:0;width:auto}
  svg .handle,svg .sel-outline,svg .guide,svg .marquee{display:none}
}

/* --- адаптив --- */
@media (max-width:1360px){ button.wide{display:none} }
@media (max-width:1180px){
  aside.nav{flex-basis:210px} aside.insp{flex-basis:250px}
  .toolbar .meta{display:none}
}
@media (max-width:980px){
  body.edit aside.insp,aside.insp{position:fixed;right:0;top:52px;bottom:0;width:270px;
    z-index:30;box-shadow:var(--shadow)}
  aside.insp{display:block}
  .brand .sub{display:none}
}
@media (max-width:820px){
  .only-narrow{display:inline-block}
  aside.nav{position:fixed;left:0;top:52px;bottom:0;width:250px;z-index:40;
    transform:translateX(-102%);transition:transform .18s;box-shadow:var(--shadow)}
  body.nav-open aside.nav{transform:none}
  aside.insp{display:none}
  .palette{flex-basis:46px}
  .palette button{width:36px;height:36px}
  .stage{padding:12px}
}
@media (max-width:560px){
  .topbar{height:auto;flex-wrap:wrap;padding:6px 8px;gap:5px}
  .layout{height:auto;min-height:calc(100vh - 92px)}
  .sep,.zoomval{display:none}
  .brand{font-size:13px;max-width:52%}
}
"""

JS_CORE = r"""
'use strict';
const FS=13, LH=17, PADX=14, PADY=10, MINW=128, MINH=44, RATIO=.6, LBL=12;
const MARGIN=26, TITLE_H=34, ARROW_LEN=9, ARROW_HALF=3.6, GRID=5, PAD=60;
const STUB=20, CORNER=6;
const MONO="Consolas, 'Cascadia Mono', 'DejaVu Sans Mono', 'Courier New', monospace";
const UI="Segoe UI, 'Noto Sans', Arial, sans-serif";
/* палитры схемы: те же, что в blockwright/render.py */
const THEMES={
  light:{stroke:"#1f2933",ink:"#10151b",bg:"#ffffff",
         fill:{process:"#ffffff",io:"#eef4ff",decision:"#fff6e5",terminator:"#e9f3ec",
               predefined:"#f3eefc",preparation:"#e8f5f1",connector:"#ffffff"}},
  dark:{stroke:"#9aa4b2",ink:"#e9eef5",bg:"#11161d",
        fill:{process:"#1a212b",io:"#152436",decision:"#2c2517",terminator:"#152a20",
              predefined:"#231d33",preparation:"#14271f",connector:"#1a212b"}}};
let THEME='light';
const TH=()=>THEMES[THEME]||THEMES.light;
const KIND_RU={process:"Процесс",io:"ВводВывод",decision:"Решение",
               terminator:"Терминатор",predefined:"Подпрограмма",
               preparation:"Цикл",connector:"Соединитель"};
const KINDS=["terminator","process","io","decision","predefined","preparation","connector"];
const STORE='blockwright.v1';

/* ---------- переводы интерфейса ---------- */
const I18N={
 ru:{
  app_title:"Блок-схемы: {0}", charts_count:"схем: {0}", my_charts:"Мои схемы",
  caption:"Рисунок {0} — Блок-схема алгоритма {1}", made_by_hand:"создано вручную",
  own:"своя", search:"Поиск схемы…", props:"Свойства",
  b_undo:"Отменить (Ctrl+Z)", b_redo:"Повторить (Ctrl+Shift+Z)",
  b_copy:"Копировать", b_copy_t:"Скопировать картинку в буфер обмена",
  b_png:"PNG", b_svg:"SVG", b_svg_t:"Вектор для Word и Figma", b_print:"Печать",
  b_project:"Проект…", b_project_t:"Выгрузить правки и свои схемы в файл",
  b_open:"Открыть", b_open_t:"Загрузить проект из файла",
  b_new_t:"Создать пустую схему", b_del:"Сбросить / удалить",
  b_del_t:"Сбросить правки схемы или удалить свою схему",
  b_rename_t:"Переименовать схему", b_theme_t:"Светлая / тёмная тема",
  b_lang_t:"Язык интерфейса", b_menu_t:"Список схем",
  z_out:"Уменьшить", z_in:"Увеличить", z_fit:"Вписать",
  cap_title:"заголовок", cap_title_t:"Добавлять заголовок в экспортируемый файл",
  kind_terminator:"Начало / конец", kind_process:"Процесс", kind_io:"Ввод-вывод",
  kind_decision:"Решение", kind_predefined:"Предопределённый процесс",
  kind_preparation:"Подготовка (цикл)", kind_connector:"Соединитель",
  t_select:"Выбор и перемещение  (V)", t_connect:"Связь: щёлкните источник, затем приёмник  (C)",
  t_label:"Подпись  (T)",
  t_terminator:"Начало / конец  (1)", t_process:"Процесс  (2)", t_io:"Ввод-вывод  (3)",
  t_decision:"Решение  (4)", t_predefined:"Предопределённый процесс  (5)",
  t_preparation:"Подготовка / цикл  (6)", t_connector:"Соединитель  (7)",
  i_type:"Тип блока", i_text:"Текст", i_apply:"Применить", i_fit:"По тексту",
  i_dup:"Дублировать", i_del:"Удалить", i_shift:"сдвигать блоки ниже",
  i_reroute:"Перепроложить связи",
  i_hint_block:"Тянуть — перемещение, квадратики — размер.<br><span class=\"kbd\">Alt</span> — без привязки к сетке, <span class=\"kbd\">Shift</span> — добавить к выделению.",
  i_from:"Из", i_to:"В", i_free:"свободный конец",
  i_arrow:"Стрелка на конце", i_arrow_on:"есть", i_arrow_off:"нет",
  i_straight:"Выпрямить", i_route:"Проложить заново",
  i_hint_edge:"Кружки — узлы линии, светлые — добавить узел. Потяните крайний узел на блок, чтобы привязать линию.",
  i_label_text:"Текст подписи", i_align:"Выравнивание",
  i_left:"слева", i_center:"по центру", i_right:"справа",
  i_selected:"Выделено объектов: <b>{0}</b>", i_align_v:"Выровнять по вертикали",
  i_align_c:"По центру", i_spread:"Разложить",
  i_empty:"Щёлкните по блоку, линии или подписи, чтобы изменить их. Блок добавляется кнопками слева, связь — инструментом <b>Связь</b>: щёлкните по блоку-источнику, затем по приёмнику.",
  m_new_name:"Название новой схемы:", m_new_default:"Схема {0}",
  m_rename:"Название схемы:",
  m_del_chart:"Удалить схему «{0}»?", m_reset_chart:"Вернуть схему «{0}» к исходному виду?",
  s_new:"Создана пустая схема — добавляйте блоки слева", s_deleted:"Схема удалена",
  s_reset:"Правки сброшены", s_no_edits:"Правок нет",
  s_svg:"SVG сохранён — открывается в Figma слоями", s_png:"PNG сохранён",
  s_copied:"PNG скопирован — вставьте в отчёт (Ctrl+V)",
  s_clip_fail:"Буфер недоступен — сохраните файлом", s_png_fail:"Не удалось сделать PNG",
  s_proj_saved:"Проект сохранён — его можно перенести на другой компьютер",
  s_proj_loaded:"Проект загружен", s_proj_bad:"Файл не похож на проект",
  s_storage:"Не удалось сохранить — хранилище браузера переполнено",
  s_rerouted:"Проложено заново: {0}", s_no_links:"Связей нет",
  s_unbound:"Линия не привязана к двум блокам", s_renamed:"Схема переименована"
 },
 en:{
  app_title:"Flowcharts: {0}", charts_count:"{0} charts", my_charts:"My charts",
  caption:"Figure {0} — Flowchart of {1}", made_by_hand:"drawn by hand",
  own:"own", search:"Search chart…", props:"Properties",
  b_undo:"Undo (Ctrl+Z)", b_redo:"Redo (Ctrl+Shift+Z)",
  b_copy:"Copy", b_copy_t:"Copy the image to the clipboard",
  b_png:"PNG", b_svg:"SVG", b_svg_t:"Vector for Word and Figma", b_print:"Print",
  b_project:"Project…", b_project_t:"Export edits and own charts to a file",
  b_open:"Open", b_open_t:"Load a project file",
  b_new_t:"Create an empty chart", b_del:"Reset / delete",
  b_del_t:"Reset chart edits or delete your own chart",
  b_rename_t:"Rename the chart", b_theme_t:"Light / dark theme",
  b_lang_t:"Interface language", b_menu_t:"Chart list",
  z_out:"Zoom out", z_in:"Zoom in", z_fit:"Fit",
  cap_title:"title", cap_title_t:"Include the title in the exported file",
  kind_terminator:"Terminator", kind_process:"Process", kind_io:"Input / output",
  kind_decision:"Decision", kind_predefined:"Predefined process",
  kind_preparation:"Preparation (loop)", kind_connector:"Connector",
  t_select:"Select and move  (V)", t_connect:"Connector: click source, then target  (C)",
  t_label:"Label  (T)",
  t_terminator:"Terminator  (1)", t_process:"Process  (2)", t_io:"Input / output  (3)",
  t_decision:"Decision  (4)", t_predefined:"Predefined process  (5)",
  t_preparation:"Preparation / loop  (6)", t_connector:"Connector  (7)",
  i_type:"Block type", i_text:"Text", i_apply:"Apply", i_fit:"Fit to text",
  i_dup:"Duplicate", i_del:"Delete", i_shift:"push blocks below",
  i_reroute:"Reroute connectors",
  i_hint_block:"Drag to move, squares resize.<br><span class=\"kbd\">Alt</span> — ignore the grid, <span class=\"kbd\">Shift</span> — extend the selection.",
  i_from:"From", i_to:"To", i_free:"free end",
  i_arrow:"Arrowhead", i_arrow_on:"yes", i_arrow_off:"no",
  i_straight:"Straighten", i_route:"Reroute",
  i_hint_edge:"Circles are nodes, light ones add a node. Drag an end node onto a block to attach the connector.",
  i_label_text:"Label text", i_align:"Alignment",
  i_left:"left", i_center:"center", i_right:"right",
  i_selected:"Selected: <b>{0}</b>", i_align_v:"Align vertically",
  i_align_c:"Center", i_spread:"Distribute",
  i_empty:"Click a block, connector or label to edit it. Add blocks with the buttons on the left; for a connector pick the <b>Connector</b> tool, then click the source and the target.",
  m_new_name:"Name of the new chart:", m_new_default:"Chart {0}",
  m_rename:"Chart name:",
  m_del_chart:"Delete chart “{0}”?", m_reset_chart:"Reset chart “{0}” to its original state?",
  s_new:"Empty chart created — add blocks from the palette", s_deleted:"Chart deleted",
  s_reset:"Edits discarded", s_no_edits:"Nothing was edited",
  s_svg:"SVG saved — opens in Figma as layers", s_png:"PNG saved",
  s_copied:"PNG copied — paste it into your report (Ctrl+V)",
  s_clip_fail:"Clipboard unavailable — save the file instead", s_png_fail:"Could not render PNG",
  s_proj_saved:"Project saved — you can move it to another computer",
  s_proj_loaded:"Project loaded", s_proj_bad:"This file is not a project",
  s_storage:"Could not save — browser storage is full",
  s_rerouted:"Rerouted: {0}", s_no_links:"No connectors",
  s_unbound:"The connector is not attached to two blocks", s_renamed:"Chart renamed"
 }};
let LANG='ru';
function t(key){
  const dict=I18N[LANG]||I18N.ru;
  let s=dict[key]!==undefined?dict[key]:(I18N.ru[key]!==undefined?I18N.ru[key]:key);
  for(let i=1;i<arguments.length;i++)s=s.split('{'+(i-1)+'}').join(arguments[i]);
  return s;
}
const KIND_LABEL=k=>t('kind_'+k);

/* ---------- текст и размеры ---------- */
function norm(s){return String(s==null?'':s).replace(/[\r\n\t]/g,' ')
  .replace(/\s+/g,' ').replace(/\s*,\s*/g,', ').trim();}
function hardSplit(tok,w){
  const parts=[];let cur='';
  for(const p of tok.split(/(?<=[,;.:_>])/)){if(!p)continue;
    if(cur&&cur.length+p.length>w){parts.push(cur);cur=p;}else cur+=p;}
  if(cur)parts.push(cur);
  const out=[];
  for(let p of parts){while(p.length>w){out.push(p.slice(0,w));p=p.slice(w);}if(p)out.push(p);}
  return out.length?out:[tok];
}
function wrap(text,w){
  text=norm(text); if(!text)return[''];
  if(text.length<=w)return[text];
  const lines=[];let cur='';
  for(const word of text.split(' ')){
    if(word.length>w){if(cur){lines.push(cur);cur='';}
      const ch=hardSplit(word,w);lines.push(...ch.slice(0,-1));cur=ch[ch.length-1];continue;}
    const cand=cur?cur+' '+word:word;
    if(cand.length<=w)cur=cand;else{lines.push(cur);cur=word;}}
  if(cur)lines.push(cur);
  return lines;
}
const r2=v=>Math.round(v*100)/100;
const n=v=>v.toFixed(2).replace(/\.?0+$/,'');
function sizeFor(kind,text,maxChars){
  const lines=wrap(text,maxChars);
  const tw=Math.max(...lines.map(l=>l.length))*FS*RATIO, th=lines.length*LH;
  let w,h;
  if(kind==='connector'){const d=Math.max(40,tw+16,th+16);w=d;h=d;}
  else if(kind==='decision'){h=Math.max(58,th*2+18);w=Math.max(150,tw*1.75+28);}
  else if(kind==='preparation'){h=Math.max(MINH,th+2*PADY);w=Math.max(MINW,tw+2*PADX+h*.8);}
  else if(kind==='io'){h=Math.max(MINH,th+2*PADY);w=Math.max(MINW,tw+2*PADX+h*.5);}
  else if(kind==='predefined'){h=Math.max(MINH,th+2*PADY);w=Math.max(MINW,tw+2*PADX+28);}
  else if(kind==='terminator'){h=Math.max(42,th+2*PADY-2);w=Math.max(MINW,tw+2*PADX+h*.6);}
  else{h=Math.max(MINH,th+2*PADY);w=Math.max(MINW,tw+2*PADX);}
  return{w:r2(w),h:r2(h),lines};
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
  .replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function slug(t,lim){lim=lim||28;
  const s=String(t||'').trim().replace(/[^0-9A-Za-zА-Яа-яЁё_-]+/g,'_')
    .replace(/_+/g,'_').replace(/^_|_$/g,'');
  return s.slice(0,lim)||'блок';}
let _uid=0; const uid=p=>p+'_'+(Date.now()%100000).toString(36)+(_uid++).toString(36);
const clone=o=>JSON.parse(JSON.stringify(o));

/* ---------- отрисовка ---------- */
function bbox(m){
  let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;
  const put=(x,y)=>{if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y;};
  for(const s of m.shapes){put(s.x,s.y);put(s.x+s.w,s.y+s.h);}
  for(const e of m.edges)for(const p of e.points)put(p[0],p[1]);
  for(const l of m.labels){const w=l.text.length*LBL*.6;
    if(l.anchor==='start'){put(l.x,l.y);put(l.x+w,l.y);}
    else if(l.anchor==='end'){put(l.x-w,l.y);put(l.x,l.y);}
    else{put(l.x-w/2,l.y);put(l.x+w/2,l.y);}
    put(l.x,l.y-LBL);}
  if(!isFinite(x0))return{x0:0,y0:0,x1:200,y1:120};
  return{x0,y0,x1,y1};
}
function outline(s){
  const x=s.x,y=s.y,w=s.w,h=s.h,k=s.kind;
  const st=`fill="${TH().fill[k]||TH().bg}" stroke="${TH().stroke}" stroke-width="1.6"`;
  if(k==='terminator')return[`<rect x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}" rx="${n(h/2)}" ry="${n(h/2)}" ${st}/>`];
  if(k==='decision')return[`<polygon points="${n(x+w/2)},${n(y)} ${n(x+w)},${n(y+h/2)} ${n(x+w/2)},${n(y+h)} ${n(x)},${n(y+h/2)}" ${st}/>`];
  if(k==='io'){const s2=Math.min(h*.34,w*.3);
    return[`<polygon points="${n(x+s2)},${n(y)} ${n(x+w)},${n(y)} ${n(x+w-s2)},${n(y+h)} ${n(x)},${n(y+h)}" ${st}/>`];}
  if(k==='preparation'){const c=Math.min(h*.5,w*.25);
    return[`<polygon points="${n(x+c)},${n(y)} ${n(x+w-c)},${n(y)} ${n(x+w)},${n(y+h/2)} ${n(x+w-c)},${n(y+h)} ${n(x+c)},${n(y+h)} ${n(x)},${n(y+h/2)}" ${st}/>`];}
  if(k==='predefined'){const o=[`<rect x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}" ${st}/>`];
    for(const dx of[11,w-11])o.push(`<line x1="${n(x+dx)}" y1="${n(y)}" x2="${n(x+dx)}" y2="${n(y+h)}" stroke="${TH().stroke}" stroke-width="1.4"/>`);
    return o;}
  if(k==='connector')return[`<circle cx="${n(x+w/2)}" cy="${n(y+h/2)}" r="${n(Math.min(w,h)/2)}" ${st}/>`];
  return[`<rect x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}" rx="2" ry="2" ${st}/>`];
}
function shapeText(s,maxChars){
  const lines=wrap(s.text,maxChars);
  const cx=s.x+s.w/2, cy=s.y+s.h/2, y0=cy-(lines.length-1)*LH/2+FS*.36;
  return lines.map((ln,i)=>`<text x="${n(cx)}" y="${n(y0+i*LH)}" text-anchor="middle" font-family="${MONO}" font-size="${FS}" fill="${TH().ink}">${esc(ln)}</text>`);
}
function cleanPts(pts){
  const cl=[pts[0]];
  for(const p of pts.slice(1)){const q=cl[cl.length-1];
    if(Math.abs(p[0]-q[0])>.01||Math.abs(p[1]-q[1])>.01)cl.push(p);}
  return cl;
}
/* полилиния со скруглёнными углами — углы 90° выглядят мягче и ровнее */
function roundPath(pts,r){
  if(pts.length<3)
    return 'M'+pts.map(p=>n(p[0])+','+n(p[1])).join(' L');
  let d='M'+n(pts[0][0])+','+n(pts[0][1]);
  for(let i=1;i<pts.length-1;i++){
    const a=pts[i-1],c=pts[i],b=pts[i+1];
    const l1=Math.hypot(c[0]-a[0],c[1]-a[1]),l2=Math.hypot(b[0]-c[0],b[1]-c[1]);
    const cross=Math.abs((c[0]-a[0])*(b[1]-c[1])-(c[1]-a[1])*(b[0]-c[0]));
    const rr=Math.min(r,l1/2,l2/2);
    if(rr<1||cross<1||!l1||!l2){d+=' L'+n(c[0])+','+n(c[1]);continue;}
    d+=' L'+n(c[0]+(a[0]-c[0])/l1*rr)+','+n(c[1]+(a[1]-c[1])/l1*rr)+
       ' Q'+n(c[0])+','+n(c[1])+' '+
       n(c[0]+(b[0]-c[0])/l2*rr)+','+n(c[1]+(b[1]-c[1])/l2*rr);
  }
  const last=pts[pts.length-1];
  return d+' L'+n(last[0])+','+n(last[1]);
}
function edgeSvg(e){
  if(e.points.length<2)return[];
  let pts=cleanPts(e.points); if(pts.length<2)return[];
  const out=[];
  if(e.arrow!==false){
    const a=pts[pts.length-2],b=pts[pts.length-1];
    const dx=b[0]-a[0],dy=b[1]-a[1],L=Math.hypot(dx,dy)||1;
    const ux=dx/L,uy=dy/L,bx=b[0]-ux*ARROW_LEN,by=b[1]-uy*ARROW_LEN;
    const px=-uy*ARROW_HALF,py=ux*ARROW_HALF;
    if(L>ARROW_LEN)pts=pts.slice(0,-1).concat([[bx,by]]);
    out.push(`<path d="M${n(b[0])},${n(b[1])} L${n(bx+px)},${n(by+py)} L${n(bx-px)},${n(by-py)} Z" fill="${TH().stroke}"/>`);
  }
  out.unshift(`<path d="${roundPath(pts,CORNER)}" fill="none" stroke="${TH().stroke}" stroke-width="1.5" stroke-linecap="round"/>`);
  return out;
}
function labelSvg(l){
  return `<text x="${n(l.x)}" y="${n(l.y)}" text-anchor="${l.anchor}" font-family="${UI}" font-size="${LBL}" fill="${TH().ink}">${esc(l.text)}</text>`;
}
/* view=null -> поля по содержимому (экспорт); иначе фиксированная область (холст) */
function renderSVG(m,opt){
  opt=opt||{};
  const b=opt.view||bbox(m), title=opt.title||null;
  const top=MARGIN+(title?TITLE_H:0);
  const W=(b.x1-b.x0)+2*MARGIN, H=(b.y1-b.y0)+MARGIN+top;
  const dx=MARGIN-b.x0, dy=top-b.y0;
  const parts=[`<rect id="Фон" x="0" y="0" width="${n(W)}" height="${n(H)}" fill="${TH().bg}"/>`];
  if(title)parts.push(`<text id="Заголовок" x="${n(W/2)}" y="${n(MARGIN+6)}" text-anchor="middle" font-family="${UI}" font-size="15" font-weight="600" fill="${TH().ink}">${esc(title)}</text>`);
  const lines=[],hits=[];
  for(const e of m.edges){
    lines.push(...edgeSvg(e));
    if(opt.interactive&&e.points.length>1)
      hits.push(`<polyline class="edge-hit" data-edge="${esc(e.id)}" points="${e.points.map(p=>n(p[0])+','+n(p[1])).join(' ')}"/>`);
  }
  const labels=m.labels.map(l=>opt.interactive
    ?`<g data-label="${esc(l.id)}" style="cursor:move">${labelSvg(l)}</g>`:labelSvg(l));
  const shapes=m.shapes.map((s,i)=>{
    const gid=`${String(i+1).padStart(2,'0')}_${KIND_RU[s.kind]||'Блок'}_${slug(s.text)}`;
    const inner=outline(s).concat(shapeText(s,m.maxChars)).join('\n  ');
    const extra=opt.interactive?` class="shp" data-shape="${esc(s.id)}"`:'';
    return `<g id="${esc(gid)}"${extra}>\n  ${inner}\n</g>`;});
  parts.push(`<g id="${esc(slug(opt.name||'Блок-схема',48))}" transform="translate(${n(dx)},${n(dy)})">`);
  parts.push('<g id="Связи">\n'+lines.join('\n')+'\n</g>');
  if(labels.length)parts.push('<g id="Подписи">\n'+labels.join('\n')+'\n</g>');
  parts.push('<g id="Блоки">\n'+shapes.join('\n')+'\n</g>');
  if(opt.interactive){parts.push('<g id="__hit">\n'+hits.join('\n')+'\n</g>');
                      parts.push('<g id="__ui"></g>');}
  parts.push('</g>');
  const head=`<svg xmlns="http://www.w3.org/2000/svg" width="${n(W)}" height="${n(H)}" viewBox="0 0 ${n(W)} ${n(H)}" role="img">`;
  return{svg:head+'\n'+parts.join('\n')+'\n</svg>',w:W,h:H,dx,dy};
}

/* ---------- модель: привязки и маршруты ---------- */
function anchors(s){return{top:[s.x+s.w/2,s.y],bottom:[s.x+s.w/2,s.y+s.h],
  left:[s.x,s.y+s.h/2],right:[s.x+s.w,s.y+s.h/2]};}
function anchorPt(m,ref){
  const s=m.shapes.find(x=>x.id===ref.id); if(!s)return null;
  return anchors(s)[ref.port]||null;
}
function hydrate(m){
  m.maxChars=m.maxChars||38;
  m.shapes=m.shapes||[];m.edges=m.edges||[];m.labels=m.labels||[];
  for(const s of m.shapes)if(!s.id)s.id=uid('s');
  for(const l of m.labels){
    if(!l.id)l.id=uid('l');
    if(l.near===undefined)l.near=nearestAnchor(m,l);
  }
  for(const e of m.edges){
    if(!e.id)e.id=uid('e');
    if(e.arrow===undefined)e.arrow=true;
    if(e.from===undefined)e.from=findAnchor(m,e.points[0]);
    if(e.to===undefined)e.to=e.arrow?findAnchor(m,e.points[e.points.length-1]):null;
  }
  return m;
}
/* подпись считается «приклеенной» к вершине блока, если стоит вплотную к ней */
function nearestAnchor(m,l){
  let best=null,bd=34;
  for(const s of m.shapes){
    const a=anchors(s);
    for(const port of['left','right','top','bottom']){
      const d=Math.hypot(a[port][0]-l.x,a[port][1]-l.y);
      if(d<bd){bd=d;best={id:s.id,port,ox:r2(l.x-a[port][0]),oy:r2(l.y-a[port][1])};}
    }
  }
  return best;
}
function findAnchor(m,pt,tol){
  tol=tol||3; let best=null,bd=tol;
  for(const s of m.shapes){
    const a=anchors(s);
    for(const port of['top','bottom','left','right']){
      const d=Math.hypot(a[port][0]-pt[0],a[port][1]-pt[1]);
      if(d<=bd){bd=d;best={id:s.id,port};}
    }
  }
  return best;
}
/* убирает узлы, лежащие на прямой между соседями */
function simplify(e){
  const p=e.points;
  for(let i=p.length-2;i>0;i--){
    if((i===1&&e.from)||(i===p.length-2&&e.to))continue;   // прямой подход к блоку
    const a=p[i-1],b=p[i],c=p[i+1];
    if((Math.abs(a[0]-b[0])<.6&&Math.abs(b[0]-c[0])<.6)||
       (Math.abs(a[1]-b[1])<.6&&Math.abs(b[1]-c[1])<.6))p.splice(i,1);
  }
}
const NORMAL={top:[0,-1],bottom:[0,1],left:[-1,0],right:[1,0]};
/* Линия обязана подходить к блоку строго по нормали к его стороне и иметь
   прямой участок: иначе стрелка «косит», а линия норовит уйти назад сквозь
   фигуру. Если подход испорчен, ближний кусок прокладывается заново:
   выход по нормали -> поворот -> ближайший «живой» узел линии. */
function fixEnd(e,isFrom){
  const ref=isFrom?e.from:e.to; if(!ref)return;
  const nrm=NORMAL[ref.port]; if(!nrm||e.points.length<2)return;
  const last=e.points.length-1;
  const idx=isFrom?0:last, j=isFrom?1:last-1;
  const p=e.points[idx], q=e.points[j];
  const along=(q[0]-p[0])*nrm[0]+(q[1]-p[1])*nrm[1];
  const side=(q[0]-p[0])*nrm[1]-(q[1]-p[1])*nrm[0];
  if(Math.abs(side)<.6&&along>=STUB-.6)return;      // подход уже правильный
  let k=j;                                          // опорный узел
  if(along<0&&e.points.length>2)k=isFrom?2:last-2;  // сосед оказался позади
  const target=e.points[k];
  const s=[r2(p[0]+nrm[0]*STUB),r2(p[1]+nrm[1]*STUB)];
  const vert=(nrm[0]===0);
  const mid=vert?[r2(target[0]),s[1]]:[s[0],r2(target[1])];
  const ins=[s];
  if(Math.hypot(mid[0]-s[0],mid[1]-s[1])>.6&&
     Math.hypot(mid[0]-target[0],mid[1]-target[1])>.6)ins.push(mid);
  if(isFrom)e.points.splice(1,k-1,...ins);
  else e.points.splice(k+1,last-k-1,...ins.reverse());
}
/* Запасной путь, когда libavoid недоступен: конец линии переезжает к новой
   точке, соседний узел подтягивается следом, если стоял с ним на одной
   прямой (и если это не чужой привязанный конец), а подход к блоку
   выправляется по нормали. */
function followEnd(e,idx,np){
  const old=e.points[idx].slice();
  const dx=np[0]-old[0], dy=np[1]-old[1];
  if(!dx&&!dy)return;
  e.points[idx]=[r2(np[0]),r2(np[1])];
  const j=idx===0?1:idx-1;
  if(j<0||j>e.points.length-1)return;
  if((j===0&&e.from)||(j===e.points.length-1&&e.to))return;
  const q=e.points[j];
  if(Math.abs(q[0]-old[0])<1.2)q[0]=r2(q[0]+dx);
  if(Math.abs(q[1]-old[1])<1.2)q[1]=r2(q[1]+dy);
}
function followShapes(m,e){
  for(const idx of [0,e.points.length-1]){
    const ref=idx===0?e.from:e.to; if(!ref)continue;
    const np=anchorPt(m,ref); if(np)followEnd(e,idx,np);
  }
  fixEnd(e,true);fixEnd(e,false);simplify(e);
}

/* ---------- геометрия линий ---------- */
function nearestOn(pts,p){
  let best=null;
  for(let i=0;i+1<pts.length;i++){
    const a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1],L=dx*dx+dy*dy;
    const t=L?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L)):0;
    const q=[a[0]+t*dx,a[1]+t*dy], d=Math.hypot(p[0]-q[0],p[1]-q[1]);
    if(!best||d<best.d)best={d,p:[r2(q[0]),r2(q[1])]};
  }
  return best;
}
const onLine=(pts,p)=>{const r=nearestOn(pts,p);return !!r&&r.d<.8;};
function freeEnds(e){
  const last=e.points.length-1, out=[];
  if(!e.from)out.push(0);
  if(!e.to&&last>0)out.push(last);
  return out;
}
/* пересекает ли ломаная блок (отрезок против прямоугольника, Лианг — Барски) */
function crosses(pts,s){
  const x0=s.x+1,y0=s.y+1,x1=s.x+s.w-1,y1=s.y+s.h-1;
  for(let i=0;i+1<pts.length;i++){
    const a=pts[i],b=pts[i+1],dx=b[0]-a[0],dy=b[1]-a[1];
    let t0=0,t1=1,ok=true;
    for(const[p,q]of[[-dx,a[0]-x0],[dx,x1-a[0]],[-dy,a[1]-y0],[dy,y1-a[1]]]){
      if(Math.abs(p)<1e-9){if(q<0){ok=false;break;}continue;}
      const r=q/p;
      if(p<0){if(r>t1){ok=false;break;}if(r>t0)t0=r;}
      else{if(r<t0){ok=false;break;}if(r<t1)t1=r;}
    }
    if(ok&&t0<=t1)return true;
  }
  return false;
}
/* Раскладка рисует одну связь несколькими кусками: «шина» ветвления, стык
   в точке на другой линии. Такие куски, соединённые свободными концами,
   образуют одну конструкцию. */
function edgeGroups(m){
  const E=m.edges, par=E.map((_,i)=>i);
  const f=i=>par[i]===i?i:(par[i]=f(par[i]));
  E.forEach((b,i)=>{for(const idx of freeEnds(b)){const p=b.points[idx];
    E.forEach((a,j)=>{if(i!==j&&onLine(a.points,p))par[f(i)]=f(j);});}});
  const g=new Map();
  E.forEach((e,i)=>{const k=f(i);if(!g.has(k))g.set(k,[]);g.get(k).push(e);});
  return [...g.values()];
}
/* свободные концы других линий, лежащие на перекладываемых */
function junctions(m,list){
  const out=[];
  for(const b of m.edges)for(const idx of freeEnds(b)){
    const host=list.find(a=>a!==b&&onLine(a.points,b.points[idx]));
    if(host)out.push({edge:b,idx,host});
  }
  return out;
}
function portAt(s,p){
  const A=anchors(s);let best='bottom',bd=Infinity;
  for(const port of PORTS){const d=Math.hypot(A[port][0]-p[0],A[port][1]-p[1]);
    if(d<bd){bd=d;best=port;}}
  return best;
}

/* ---------- трассировка: libavoid ----------
   Маршруты считает libavoid из Adaptagrams — тот же трассировщик, что в
   Inkscape: ортогональные линии обходят блоки, выходят и входят строго по
   нормали к стороне, а идущие рядом расходятся на равный шаг. Библиотека
   собрана в WebAssembly (vendor/web/libavoid) и встроена в страницу, так
   что работает и с file://, и без сети. Если браузер её не загрузил,
   действует простой запасной алгоритм (followShapes / autoRoute). */
let AV=null;
const PORTS=['top','bottom','left','right'];
const PIN={top:[.5,0,1],bottom:[.5,1,2],left:[0,.5,4],right:[1,.5,8]};  // x, y, ConnDir
const CLS={top:10,bottom:11,left:12,right:13,out:20,in:21};   // 1 у libavoid занят
const AV_BUF=12, AV_SIDE=40;     // отступ от блоков; «цена» выхода вбок
function loadRouter(){
  if(AV||typeof AvoidModule!=='function'||typeof AVOID_WASM!=='string'||
     typeof WebAssembly!=='object')return Promise.resolve(AV);
  let bin;
  try{bin=Uint8Array.from(atob(AVOID_WASM),c=>c.charCodeAt(0));}
  catch(e){return Promise.resolve(null);}
  return AvoidModule({print(){},printErr(){},onAbort(){AV=null;},
    instantiateWasm(imports,done){
      WebAssembly.instantiate(bin,imports).then(r=>done(r.instance,r.module),()=>{});
      return {};}})
    .then(A=>{AV=A;return A;},()=>null);
}
const straightOnly=pts=>pts.length>1&&pts.every((p,i)=>!i||
  Math.abs(p[0]-pts[i-1][0])<.6||Math.abs(p[1]-pts[i-1][1])<.6);
/* «шпилька»: линия доходит до точки и возвращается назад по той же прямой */
function spiky(pts){
  for(let i=1;i+1<pts.length;i++){
    const a=pts[i-1],b=pts[i],c=pts[i+1];
    const ux=b[0]-a[0],uy=b[1]-a[1],vx=c[0]-b[0],vy=c[1]-b[1];
    if(Math.abs(ux*vy-uy*vx)<.5&&ux*vx+uy*vy<0)return true;
  }
  return false;
}
/* Опорные точки (checkpoints) — изломы прежнего маршрута: линия, которую
   задел блок, обходит его рядом, а не уходит «кратчайшим» путём через всю
   схему. Излом у сдвинутого конца и изломы позади него отбрасываются —
   иначе линия ломалась бы назад. moved — индексы сдвинутых свободных концов. */
function checkpoints(m,e,moved){
  const P=e.points, last=P.length-1;
  if(last<2)return [];
  let lo=1, hi=last-1;
  const guard=[null,null];
  [[0,e.from],[last,e.to]].forEach(([idx,ref],k)=>{
    const s=ref&&m.shapes.find(x=>x.id===ref.id);
    let shifted=!!(moved&&moved.has(idx));
    if(s){const a=anchors(s)[ref.port];
      shifted=Math.hypot(a[0]-P[idx][0],a[1]-P[idx][1])>.6;
      if(shifted)guard[k]=[a,NORMAL[ref.port]];}
    if(shifted){if(idx===0)lo=2;else hi=last-2;}
  });
  const B=AV_BUF-1, out=[];
  for(let i=lo;i<=hi;i++){
    const p=P[i];
    if(!m.shapes.some(s=>p[0]>s.x-B&&p[0]<s.x+s.w+B&&p[1]>s.y-B&&p[1]<s.y+s.h+B))out.push(p);
  }
  /* ближайшие к сдвинутому блоку точки не должны оказаться позади его стороны */
  const behind=(p,g)=>g&&(p[0]-g[0][0])*g[1][0]+(p[1]-g[0][1])*g[1][1]<AV_BUF;
  while(out.length&&behind(out[0],guard[0]))out.shift();
  while(out.length&&behind(out[out.length-1],guard[1]))out.pop();
  return out;
}
/* reqs: [{from,to,a,b}], from/to — {id,cls} или null (тогда конец — точка a/b).
   Возвращает маршруты; null там, где libavoid пути не нашёл. */
function avRoute(m,reqs,buf){
  const A=AV, P=A.RoutingParameter, tmp=[], T=o=>(tmp.push(o),o);
  const multi=reqs.some(q=>[q.from,q.to].some(r=>r&&(r.cls===CLS.out||r.cls===CLS.in)));
  const R=new A.Router(A.RouterFlag.OrthogonalRouting.value);
  try{
    R.setRoutingParameter(P.shapeBufferDistance,buf||AV_BUF);
    R.setRoutingParameter(P.idealNudgingDistance,10);
    R.setRoutingParameter(P.segmentPenalty,50);
    /* в блок-схеме линии сходятся в середину стороны (вход цикла и
       обратная связь), поэтому концы у блоков не раздвигаются */
    R.setRoutingOption(A.RoutingOption.nudgeOrthogonalSegmentsConnectedToShapes,false);
    const refs={};
    for(const s of m.shapes){
      const ref=new A.ShapeRef(R,T(new A.Rectangle(T(new A.Point(s.x,s.y)),
                                                   T(new A.Point(s.x+s.w,s.y+s.h)))));
      for(const port of PORTS){
        const[px,py,dir]=PIN[port];
        const pin=(cls,cost)=>{const p=new A.ShapeConnectionPin(ref,cls,px,py,true,0,dir);
          p.setExclusive(false); if(cost)p.setConnectionCost(cost);};
        pin(CLS[port],0);
        if(!multi)continue;
        if(port!=='top')pin(CLS.out,port==='bottom'?0:AV_SIDE);
        if(port!=='bottom')pin(CLS.in,port==='top'?0:AV_SIDE);
      }
      refs[s.id]=ref;
    }
    const end=(r,p)=>r&&refs[r.id]?T(new A.ConnEnd(refs[r.id],r.cls))
                                  :T(new A.ConnEnd(T(new A.Point(p[0],p[1]))));
    const conns=reqs.map(q=>{const c=new A.ConnRef(R,end(q.from,q.a),end(q.to,q.b));
      c.setRoutingType(A.ConnType.ConnType_Orthogonal);
      if(q.cps&&q.cps.length){
        const v=T(new A.CheckpointVector());
        for(const p of q.cps)v.push_back(T(new A.Checkpoint(T(new A.Point(p[0],p[1])))));
        c.setRoutingCheckpoints(v);
      }
      return c;});
    R.processTransaction();
    /* конец маршрута обязан стоять на точке привязки блока или на своей точке */
    const S=id=>m.shapes.find(s=>s.id===id);
    const near=(p,q)=>Math.hypot(p[0]-q[0],p[1]-q[1])<.6;
    const lands=(r,q,p)=>r&&refs[r.id]?Object.values(anchors(S(r.id))).some(a=>near(a,p))
                                      :near(q,p);
    return conns.map((c,i)=>{
      const r=T(c.displayRoute()),pts=[];
      for(let k=0;k<r.size();k++){const p=T(r.at(k));pts.push([r2(p.x),r2(p.y)]);}
      const cl=cleanPts(pts), q=reqs[i];
      return c.hasValidRoute()&&straightOnly(cl)&&!spiky(cl)&&lands(q.from,q.a,cl[0])&&
             lands(q.to,q.b,cl[cl.length-1])?cl:null;});
  }finally{
    for(const o of tmp)try{o.delete();}catch(e){}
    R.delete();
  }
}
function avRun(m,reqs,buf){
  if(!AV||!reqs.length)return null;
  try{return avRoute(m,reqs,buf);}catch(e){AV=null;return null;}   // сломался — дальше без него
}
/* концы линии для трассировщика.
   mode: 'keep' — те же стороны блоков; 'free' — сторону выбирает libavoid
   (выход снизу или вбок, вход сверху или вбок; у ромба стороны значат
   «Да»/«Нет» и не меняются); 'guess' — стороны по простой эвристике. */
function endsOf(m,e,mode){
  const P=e.points, S=id=>m.shapes.find(s=>s.id===id);
  let fp=e.from&&e.from.port, tp=e.to&&e.to.port;
  if(mode==='guess'&&e.from&&e.to&&S(e.from.id)&&S(e.to.id)){
    const r=autoRoute(m,S(e.from.id),S(e.to.id));
    if(S(e.from.id).kind!=='decision')fp=r.from;
    tp=r.to;
  }
  const ref=(r,port,dflt)=>{
    if(!r||!S(r.id))return null;
    if(mode==='free')return{id:r.id,cls:dflt&&S(r.id).kind!=='decision'?dflt:CLS[port]};
    return{id:r.id,cls:CLS[port]};
  };
  return{from:ref(e.from,fp,CLS.out),to:ref(e.to,tp,CLS.in),a:P[0],b:P[P.length-1]};
}
/* Отступ линий от блоков. Если блок придвинут к соседу теснее двух
   отступов, линия между ними не пролезла бы и ушла в большой обход —
   тогда отступ уменьшается до половины зазора. */
function bufferFor(m,list){
  const ids=new Set(list.flatMap(e=>[e.from,e.to]).filter(Boolean).map(r=>r.id));
  let gap=Infinity;
  for(const a of m.shapes){
    if(!ids.has(a.id))continue;
    for(const b of m.shapes){
      if(b===a)continue;
      const dx=Math.max(b.x-a.x-a.w,a.x-b.x-b.w), dy=Math.max(b.y-a.y-a.h,a.y-b.y-b.h);
      const d=Math.max(dx,dy);             // зазор между прямоугольниками
      if(d>=0)gap=Math.min(gap,d);
    }
  }
  return Math.max(3,Math.min(AV_BUF,Math.floor(gap/2)-1));
}
/* Прокладывает линии заново.
   opt.free  — разрешить смену сторон (кнопка «Проложить заново», новая
               связь); иначе стороны блоков сохраняются;
   opt.fresh — линия новая: к ней ещё ничего не примыкает;
   opt.moved — Map(линия -> индексы свободных концов, которые сдвинулись). */
function routeEdges(m,list,opt){
  opt=opt||{};
  const free=!!opt.free, depth=opt.depth||0, moved=opt.moved;
  list=list.filter(e=>e.points.length>1);
  if(!list.length)return;
  const glue=opt.fresh?[]:junctions(m,list);
  const buf=bufferFor(m,list);
  const reqs=list.map(e=>endsOf(m,e,free?'free':'keep'));
  if(!free)reqs.forEach((q,i)=>{q.cps=checkpoints(m,list[i],moved&&moved.get(list[i]));});
  const res=avRun(m,reqs,buf)||[];
  /* где не вышло — ещё попытки: без опорных точек (при свободном выборе —
     со сторонами по эвристике: libavoid порой спотыкается на нём), затем
     с малым отступом — когда блоки стоят почти вплотную */
  const retry=pad=>{
    const bad=list.map((e,i)=>res[i]?-1:i).filter(i=>i>=0);
    if(!AV||!bad.length)return;
    const again=avRun(m,bad.map(i=>free?endsOf(m,list[i],'guess')
                                       :Object.assign({},reqs[i],{cps:[]})),pad)||[];
    bad.forEach((i,k)=>{res[i]=again[k]||null;});
  };
  retry(buf); retry(Math.min(4,buf));
  list.forEach((e,i)=>{
    const pts=res[i];
    if(pts){
      e.points=pts;
      const S=id=>m.shapes.find(s=>s.id===id);
      if(e.from&&S(e.from.id))e.from.port=portAt(S(e.from.id),pts[0]);
      if(e.to&&S(e.to.id))e.to.port=portAt(S(e.to.id),pts[pts.length-1]);
    }else if(free&&e.from&&e.to)legacyReroute(m,e);
    else followShapes(m,e);
  });
  /* примыкавшие линии дотягиваются до нового хода — стык не отрывается
     (если он не лежит и на какой-то другой линии: тогда держится за неё) */
  const again=new Map();
  for(const g of glue){
    const p=g.edge.points[g.idx];
    if(m.edges.some(a=>a!==g.edge&&onLine(a.points,p)))continue;
    const q=nearestOn(g.host.points,p); if(!q)continue;
    if(AV)g.edge.points[g.idx]=q.p; else followEnd(g.edge,g.idx,q.p);
    if(!again.has(g.edge))again.set(g.edge,new Set());
    again.get(g.edge).add(g.idx);
  }
  if(again.size&&depth<3){
    if(AV)routeEdges(m,[...again.keys()],{depth:depth+1,moved:again});
    else again.forEach((_,e)=>simplify(e));
  }
}
function legacyReroute(m,e){
  const a=m.shapes.find(s=>s.id===e.from.id), b=m.shapes.find(s=>s.id===e.to.id);
  if(!a||!b)return false;
  const r=autoRoute(m,a,b);
  e.points=r.pts.map(p=>[r2(p[0]),r2(p[1])]);
  e.from={id:a.id,port:r.from}; e.to={id:b.id,port:r.to};
  return true;
}
/* Блоки shapeIds сдвинулись или изменили размер — линии следуют за ними.
   opt.delta — общий сдвиг: конструкция, все блоки которой едут вместе,
   просто переносится, а не перекладывается. opt.skip — линии, которые
   уже сдвинуты вручную. */
function syncEdges(m,shapeIds,opt){
  opt=opt||{};
  const ids=new Set(shapeIds), skip=new Set(opt.skip||[]);
  /* подписи «Да»/«Нет» приклеены к вершинам блока и едут вместе с ним */
  for(const l of m.labels){
    if(!l.near||!ids.has(l.near.id))continue;
    const s=m.shapes.find(x=>x.id===l.near.id); if(!s)continue;
    const a=anchors(s)[l.near.port]; if(!a)continue;
    l.x=r2(a[0]+l.near.ox); l.y=r2(a[1]+l.near.oy);
  }
  if(!ids.size)return;
  const d=opt.delta;
  if(d&&(d[0]||d[1]))for(const g of edgeGroups(m)){
    const refs=g.flatMap(e=>[e.from,e.to]).filter(Boolean);
    if(!refs.length||!refs.every(r=>ids.has(r.id)))continue;
    for(const e of g){
      if(!skip.has(e.id))e.points=e.points.map(p=>[r2(p[0]+d[0]),r2(p[1]+d[1])]);
      skip.add(e.id);
    }
  }
  const moved=m.shapes.filter(s=>ids.has(s.id));
  const list=m.edges.filter(e=>!skip.has(e.id)&&(
    (e.from&&ids.has(e.from.id))||(e.to&&ids.has(e.to.id))||
    moved.some(s=>crosses(e.points,s))));
  routeEdges(m,list);
}
/* проложить линию заново: концы у блоков, стороны — какие удобнее */
function rerouteEdge(m,e,fresh){
  if(!e.from||!e.to)return false;
  if(!m.shapes.some(s=>s.id===e.from.id)||!m.shapes.some(s=>s.id===e.to.id))return false;
  routeEdges(m,[e],{free:true,fresh});
  return true;
}
function autoRoute(m,a,b){
  const A=anchors(a),B=anchors(b);
  if(b.y>a.y+a.h-2){
    const mid=r2((a.y+a.h+b.y)/2);
    if(Math.abs(A.bottom[0]-B.top[0])<2)return{pts:[A.bottom,B.top],from:'bottom',to:'top'};
    return{pts:[A.bottom,[A.bottom[0],mid],[B.top[0],mid],B.top],from:'bottom',to:'top'};
  }
  if(b.y+b.h<a.y+2){
    const side=r2(Math.min(a.x,b.x)-34), y1=r2(a.y+a.h+20), y2=r2(b.y-20);
    return{pts:[A.bottom,[A.bottom[0],y1],[side,y1],[side,y2],[B.top[0],y2],B.top],
           from:'bottom',to:'top'};
  }
  const right=b.x>a.x;
  const p1=right?A.right:A.left, p2=right?B.left:B.right;
  const mx=r2((p1[0]+p2[0])/2);
  return{pts:[p1,[mx,p1[1]],[mx,p2[1]],p2],from:right?'right':'left',
         to:right?'left':'right'};
}
/* «разрезать» схему по горизонтали и раздвинуть — когда блок стал выше */
function shiftBelow(m,threshold,delta){
  if(!delta)return;
  for(const s of m.shapes)if(s.y>=threshold-.5)s.y=r2(s.y+delta);
  for(const e of m.edges)e.points=e.points.map(p=>
    [p[0],p[1]>=threshold-.5?r2(p[1]+delta):p[1]]);
  for(const l of m.labels)if(l.y>=threshold-.5)l.y=r2(l.y+delta);
}
function newShape(kind,x,y,text,maxChars){
  const g=sizeFor(kind,text,maxChars||38);
  return{id:uid('s'),kind,text,x:r2(x-g.w/2),y:r2(y-g.h/2),w:g.w,h:g.h};
}
function emptyDoc(name){
  const m={name,rel:'мои схемы',signature:'',line:0,maxChars:38,
           shapes:[],edges:[],labels:[]};
  const a=newShape('terminator',300,80,'Начало',38);
  const b=newShape('terminator',300,320,'Конец',38);
  m.shapes.push(a,b);
  const r=autoRoute(m,a,b);
  m.edges.push({id:uid('e'),points:r.pts.map(p=>[r2(p[0]),r2(p[1])]),arrow:true,
                from:{id:a.id,port:r.from},to:{id:b.id,port:r.to}});
  return m;
}
"""

JS_APP = r"""
/* ---------- состояние ---------- */
const $=s=>document.querySelector(s);
let docs={}, custom=[], dirty=new Set(), names={}, cur=null, view=null, zoom=1;
let exportTitle=true;
let sel={shapes:new Set(),edges:new Set(),labels:new Set()};
let tool='select', hist=[], future=[], drag=null, pending=null, guides=[];

function loadStore(){
  try{const raw=JSON.parse(localStorage.getItem(STORE)||'{}');
    docs=raw.docs||{}; custom=raw.custom||[]; dirty=new Set(raw.dirty||[]);
    names=raw.names||{};
    LANG=raw.lang||DATA.lang||LANG;          // выбор пользователя важнее умолчаний,
    THEME=raw.theme||DATA.theme||THEME;      // а умолчания приходят из командной строки
    if(raw.exportTitle!==undefined)exportTitle=!!raw.exportTitle;}
  catch(e){docs={};custom=[];dirty=new Set();names={};
           LANG=DATA.lang||LANG;THEME=DATA.theme||THEME;}
  if(!I18N[LANG])LANG='ru';
  if(!THEMES[THEME])THEME='light';
}
function saveStore(){
  /* храним только то, что правили вручную, и свои схемы */
  const keep={}, mine=new Set(custom.map(c=>c.anchor));
  for(const k of Object.keys(docs))if(dirty.has(k)||mine.has(k))keep[k]=docs[k];
  try{localStorage.setItem(STORE,JSON.stringify(
    {docs:keep,custom,dirty:[...dirty],names,lang:LANG,theme:THEME,exportTitle}));}
  catch(e){toast(t('s_storage'));}
}
function entries(){
  return DATA.items.concat(custom.map(c=>({anchor:c.anchor,name:c.name,rel:t('my_charts'),
    signature:t('made_by_hand'),line:0,custom:true})));
}
function meta(){return entries().find(i=>i.anchor===cur)||{name:'',rel:'',signature:'',line:0};}
function nameOf(it){return (it&&names[it.anchor])||(it&&it.name)||'';}
function fileBase(){
  return (nameOf(meta())||cur||'chart').replace(/[^0-9A-Za-zА-Яа-яЁё_.-]+/g,'_');}
function model(){
  if(!docs[cur]){
    const it=meta();
    const base=it&&it.model?clone(it.model):emptyDoc(it?it.name:'Схема');
    docs[cur]=hydrate(base);
  }
  return docs[cur];
}
function isEdited(a){return dirty.has(a);}
function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');
  clearTimeout(t._t);t._t=setTimeout(()=>t.classList.remove('show'),2000);}

function push(){hist.push(clone(model()));if(hist.length>80)hist.shift();
  future.length=0; dirty.add(cur);}
function commit(){saveStore();draw();buildTree($('#search').value);inspect();}
function undo(){if(!hist.length)return;future.push(clone(model()));
  docs[cur]=hist.pop();clearSel();commit();}
function redo(){if(!future.length)return;hist.push(clone(model()));
  docs[cur]=future.pop();clearSel();commit();}

/* ---------- выделение ---------- */
function clearSel(){sel={shapes:new Set(),edges:new Set(),labels:new Set()};}
function selCount(){return sel.shapes.size+sel.edges.size+sel.labels.size;}
function selectOnly(kind,id){clearSel();sel[kind].add(id);}

/* ---------- отрисовка холста ---------- */
function ensureView(m,reset){
  const b=bbox(m);
  if(reset||!view){view={x0:b.x0-PAD,y0:b.y0-PAD,x1:b.x1+PAD,y1:b.y1+PAD};return;}
  view={x0:Math.min(view.x0,b.x0-PAD),y0:Math.min(view.y0,b.y0-PAD),
        x1:Math.max(view.x1,b.x1+PAD),y1:Math.max(view.y1,b.y1+PAD)};
}
function draw(){
  const m=model(); ensureView(m,false);
  const out=renderSVG(m,{interactive:true,view,name:nameOf(meta())});
  $('#sheet').innerHTML=out.svg;
  const svg=$('#sheet svg');
  svg.style.width=(out.w*zoom)+'px'; svg.style.height=(out.h*zoom)+'px';
  $('#zoomVal').textContent=Math.round(zoom*100)+'%';
  drawUI();
  svg.addEventListener('pointerdown',onDown);
  svg.addEventListener('pointermove',onMove);
  svg.addEventListener('pointerup',onUp);
  svg.addEventListener('dblclick',onDbl);
}
function ui(){return $('#__ui');}
function drawUI(){
  const g=ui(); if(!g)return;
  const m=model(); const parts=[];
  for(const id of sel.shapes){
    const s=m.shapes.find(x=>x.id===id); if(!s)continue;
    parts.push(`<rect class="sel-outline" x="${n(s.x-4)}" y="${n(s.y-4)}" width="${n(s.w+8)}" height="${n(s.h+8)}" rx="3"/>`);
    if(sel.shapes.size===1){
      const a=[[s.x+s.w,s.y+s.h/2,'e'],[s.x+s.w/2,s.y+s.h,'s'],[s.x+s.w,s.y+s.h,'se']];
      for(const [x,y,dir] of a)
        parts.push(`<rect class="handle" data-resize="${dir}" x="${n(x-4)}" y="${n(y-4)}" width="8" height="8" rx="2"/>`);
    }
  }
  for(const id of sel.edges){
    const e=m.edges.find(x=>x.id===id); if(!e)continue;
    e.points.forEach((p,i)=>{
      const bound=(i===0&&e.from)||(i===e.points.length-1&&e.to);
      parts.push(`<circle class="handle${bound?' bound':''}" data-vtx="${esc(e.id)}:${i}" cx="${n(p[0])}" cy="${n(p[1])}" r="5"/>`);
      if(i<e.points.length-1){const q=e.points[i+1];
        parts.push(`<circle class="handle mid" data-mid="${esc(e.id)}:${i}" cx="${n((p[0]+q[0])/2)}" cy="${n((p[1]+q[1])/2)}" r="3.6"/>`);}
    });
  }
  for(const id of sel.labels){
    const l=m.labels.find(x=>x.id===id); if(!l)continue;
    const w=l.text.length*LBL*.6;
    const x=l.anchor==='start'?l.x:(l.anchor==='end'?l.x-w:l.x-w/2);
    parts.push(`<rect class="sel-outline" x="${n(x-3)}" y="${n(l.y-LBL-2)}" width="${n(w+6)}" height="${n(LBL+7)}" rx="2"/>`);
  }
  for(const gd of guides)parts.push(`<line class="guide" x1="${n(gd[0])}" y1="${n(gd[1])}" x2="${n(gd[2])}" y2="${n(gd[3])}"/>`);
  if(drag&&drag.type==='marquee'){
    const[x0,y0]=drag.from,[x1,y1]=drag.at;
    parts.push(`<rect class="marquee" x="${n(Math.min(x0,x1))}" y="${n(Math.min(y0,y1))}" width="${n(Math.abs(x1-x0))}" height="${n(Math.abs(y1-y0))}"/>`);
  }
  if(pending){const a=pending.shape,A=anchors(a);
    parts.push(`<circle class="handle bound" cx="${n(A.bottom[0])}" cy="${n(A.bottom[1])}" r="5"/>`);
    if(pending.at)parts.push(`<line class="guide" x1="${n(A.bottom[0])}" y1="${n(A.bottom[1])}" x2="${n(pending.at[0])}" y2="${n(pending.at[1])}"/>`);}
  g.innerHTML=parts.join('\n');
}

/* ---------- координаты ---------- */
function pt(ev){
  const svg=$('#sheet svg'), scene=svg.querySelector('#__ui').parentNode;
  const p=svg.createSVGPoint(); p.x=ev.clientX; p.y=ev.clientY;
  const q=p.matrixTransform(scene.getScreenCTM().inverse());
  return[q.x,q.y];
}
const snap=(v,off)=>off?v:Math.round(v/GRID)*GRID;
function hitShape(m,p){
  for(let i=m.shapes.length-1;i>=0;i--){const s=m.shapes[i];
    if(p[0]>=s.x&&p[0]<=s.x+s.w&&p[1]>=s.y&&p[1]<=s.y+s.h)return s;}
  return null;
}

/* ---------- мышь ---------- */
function onDown(ev){
  if(ev.button!==0)return;
  const m=model(), p=pt(ev), t=ev.target;
  try{$('#sheet svg').setPointerCapture(ev.pointerId);}catch(e){}
  if(tool.startsWith('add:')){
    push(); const kind=tool.slice(4);
    const s=newShape(kind,snap(p[0],ev.altKey),snap(p[1],ev.altKey),
                     kind==='decision'?'условие':'действие',m.maxChars);
    m.shapes.push(s); selectOnly('shapes',s.id); setTool('select'); commit(); return;
  }
  if(tool==='label'){
    push(); const l={id:uid('l'),x:r2(p[0]),y:r2(p[1]),text:'подпись',anchor:'start'};
    m.labels.push(l); selectOnly('labels',l.id); setTool('select'); commit(); return;
  }
  if(tool==='connect'){
    const s=hitShape(m,p);
    if(!s){pending=null;drawUI();return;}
    if(!pending){pending={shape:s,at:p};drawUI();return;}
    if(pending.shape.id!==s.id){
      push(); const r=autoRoute(m,pending.shape,s);
      const e={id:uid('e'),points:r.pts.map(q=>[r2(q[0]),r2(q[1])]),arrow:true,
        from:{id:pending.shape.id,port:r.from},to:{id:s.id,port:r.to}};
      m.edges.push(e); rerouteEdge(m,e,true);
      commit();
    }
    pending=null; setTool('select'); drawUI(); return;
  }
  const resize=t.getAttribute&&t.getAttribute('data-resize');
  const vtx=t.getAttribute&&t.getAttribute('data-vtx');
  const mid=t.getAttribute&&t.getAttribute('data-mid');
  if(mid){
    const[eid,i]=mid.split(':'); const e=m.edges.find(x=>x.id===eid);
    push(); const a=e.points[+i],b=e.points[+i+1];
    e.points.splice(+i+1,0,[r2((a[0]+b[0])/2),r2((a[1]+b[1])/2)]);
    drag={type:'vtx',edge:eid,idx:+i+1}; commit(); return;
  }
  if(vtx){const[eid,i]=vtx.split(':'); push(); drag={type:'vtx',edge:eid,idx:+i};return;}
  if(resize){const id=[...sel.shapes][0]; push();
    drag={type:'resize',dir:resize,id,from:p,edges:clone(m.edges),
          orig:clone(m.shapes.find(s=>s.id===id))};return;}
  const shapeEl=t.closest&&t.closest('[data-shape]');
  const edgeEl=t.closest&&t.closest('[data-edge]');
  const labelEl=t.closest&&t.closest('[data-label]');
  if(shapeEl){
    const id=shapeEl.getAttribute('data-shape');
    if(ev.shiftKey)sel.shapes.has(id)?sel.shapes.delete(id):sel.shapes.add(id);
    else if(!sel.shapes.has(id))selectOnly('shapes',id);
    push();
    /* линии каждый раз считаются от состояния на начало перетаскивания:
       ошибки не копятся, а вернув блок на место, получаем прежние линии */
    drag={type:'move',from:p,at:p,lead:id,edges:clone(m.edges),
          orig:m.shapes.filter(s=>sel.shapes.has(s.id)).map(s=>({id:s.id,x:s.x,y:s.y})),
          origL:m.labels.filter(l=>sel.labels.has(l.id)).map(l=>({id:l.id,x:l.x,y:l.y}))};
    inspect(); drawUI(); return;
  }
  if(labelEl){
    const id=labelEl.getAttribute('data-label');
    if(!ev.shiftKey)clearSel(); sel.labels.add(id); push();
    const l=m.labels.find(x=>x.id===id);
    drag={type:'move',from:p,at:p,orig:[],origL:[{id,x:l.x,y:l.y}]};
    inspect(); drawUI(); return;
  }
  if(edgeEl){
    const id=edgeEl.getAttribute('data-edge');
    if(!ev.shiftKey)clearSel(); sel.edges.add(id);
    inspect(); drawUI(); return;
  }
  if(!ev.shiftKey)clearSel();
  drag={type:'marquee',from:p,at:p}; inspect(); drawUI();
}
/* движение обрабатывается не чаще раза за кадр: на телефоне пересчёт линий
   медленнее, и события иначе копились бы в очередь */
let moveEv=null;
function onMove(ev){
  if(!drag&&!pending)return;
  const first=!moveEv;
  moveEv={clientX:ev.clientX,clientY:ev.clientY,altKey:ev.altKey};
  if(first)requestAnimationFrame(flushMove);
}
function flushMove(){
  const ev=moveEv; moveEv=null;
  if(ev&&(drag||pending))moveNow(ev);
}
function moveNow(ev){
  const m=model(), p=pt(ev);
  if(pending){pending.at=p;drawUI();return;}
  if(drag.type==='marquee'){drag.at=p;drawUI();return;}
  if(drag.type==='move'){
    let dx=p[0]-drag.from[0], dy=p[1]-drag.from[1];
    guides=[];
    if(!ev.altKey&&drag.orig.length===1){
      const s=m.shapes.find(x=>x.id===drag.orig[0].id);
      const cx=drag.orig[0].x+dx+s.w/2;
      for(const o of m.shapes){
        if(o.id===s.id)continue;
        const ox=o.x+o.w/2;
        if(Math.abs(ox-cx)<7){dx+=ox-cx;
          guides.push([ox,Math.min(o.y,drag.orig[0].y+dy)-30,ox,
                       Math.max(o.y+o.h,drag.orig[0].y+dy+s.h)+30]);break;}
      }
    }
    /* к сетке привязывается блок под курсором, остальные едут на тот же
       сдвиг — так группа не расползается */
    const lead=drag.orig.find(o=>o.id===drag.lead)||drag.orig[0];
    if(lead){dx=r2(snap(lead.x+dx,ev.altKey||guides.length>0)-lead.x);
             dy=r2(snap(lead.y+dy,ev.altKey)-lead.y);}
    for(const o of drag.orig){const s=m.shapes.find(x=>x.id===o.id);
      s.x=r2(o.x+dx); s.y=r2(o.y+dy);}
    for(const o of drag.origL){const l=m.labels.find(x=>x.id===o.id);
      l.x=r2(o.x+dx); l.y=r2(o.y+dy);}
    m.edges=clone(drag.edges);
    syncEdges(m,drag.orig.map(o=>o.id),{delta:[dx,dy]});
    drag.at=p; redrawFast(); return;
  }
  if(drag.type==='resize'){
    const s=m.shapes.find(x=>x.id===drag.id), o=drag.orig;
    if(drag.dir!=='s')s.w=r2(Math.max(60,snap(o.w+(p[0]-drag.from[0]),ev.altKey)));
    if(drag.dir!=='e')s.h=r2(Math.max(34,snap(o.h+(p[1]-drag.from[1]),ev.altKey)));
    m.edges=clone(drag.edges);
    syncEdges(m,[s.id]); redrawFast(); return;
  }
  if(drag.type==='vtx'){
    const e=m.edges.find(x=>x.id===drag.edge); if(!e)return;
    e.points[drag.idx]=[r2(snap(p[0],ev.altKey)),r2(snap(p[1],ev.altKey))];
    if(drag.idx===0)e.from=null;
    if(drag.idx===e.points.length-1)e.to=null;
    redrawFast(); return;
  }
}
function onUp(ev){
  flushMove();               // последнее движение до отпускания
  const m=model();
  if(drag&&drag.type==='marquee'){
    const[x0,y0]=drag.from,[x1,y1]=drag.at;
    const a=[Math.min(x0,x1),Math.min(y0,y1),Math.max(x0,x1),Math.max(y0,y1)];
    if(Math.abs(x1-x0)>3||Math.abs(y1-y0)>3){
      for(const s of m.shapes)
        if(s.x>=a[0]&&s.y>=a[1]&&s.x+s.w<=a[2]&&s.y+s.h<=a[3])sel.shapes.add(s.id);
      for(const l of m.labels)
        if(l.x>=a[0]&&l.y>=a[1]&&l.x<=a[2]&&l.y<=a[3])sel.labels.add(l.id);
    }
  }
  if(drag&&drag.type==='vtx'){        // бросили конец линии на блок — привяжем
    const e=m.edges.find(x=>x.id===drag.edge);
    if(e&&(drag.idx===0||drag.idx===e.points.length-1)){
      const s=hitShape(m,e.points[drag.idx]);
      if(s){
        const A=anchors(s), p=e.points[drag.idx];
        let best='top',bd=1e9;
        for(const port of['top','bottom','left','right']){
          const d=Math.hypot(A[port][0]-p[0],A[port][1]-p[1]);
          if(d<bd){bd=d;best=port;}
        }
        e.points[drag.idx]=[r2(A[best][0]),r2(A[best][1])];
        if(drag.idx===0)e.from={id:s.id,port:best}; else e.to={id:s.id,port:best};
        routeEdges(m,[e]);     // подход к блоку — строго по нормали
      }
    }
  }
  guides=[]; drag=null; commit();
}
function onDbl(ev){
  const el=ev.target.closest&&ev.target.closest('[data-shape],[data-label]');
  if(!el)return;
  const id=el.getAttribute('data-shape')||el.getAttribute('data-label');
  clearSel();
  (el.hasAttribute('data-shape')?sel.shapes:sel.labels).add(id);
  inspect(); drawUI();
  const f=$('#fText'); if(f){f.focus();f.select();}
}
/* быстрая перерисовка во время перетаскивания — без пересборки панелей */
function redrawFast(){
  const m=model();
  const svg=$('#sheet svg'); if(!svg)return;
  const out=renderSVG(m,{interactive:true,view,name:nameOf(meta())});
  const tmp=document.createElement('div'); tmp.innerHTML=out.svg;
  svg.innerHTML=tmp.firstElementChild.innerHTML;
  drawUI();
}

/* ---------- операции ---------- */
function delSel(){
  const m=model(); if(!selCount())return; push();
  m.shapes=m.shapes.filter(s=>!sel.shapes.has(s.id));
  m.labels=m.labels.filter(l=>!sel.labels.has(l.id));
  m.edges=m.edges.filter(e=>!sel.edges.has(e.id));
  for(const e of m.edges){
    if(e.from&&sel.shapes.has(e.from.id))e.from=null;
    if(e.to&&sel.shapes.has(e.to.id))e.to=null;
  }
  clearSel(); commit();
}
function dupSel(){
  const m=model(); if(!sel.shapes.size)return; push();
  const added=[];
  for(const id of sel.shapes){
    const s=m.shapes.find(x=>x.id===id); if(!s)continue;
    const c=clone(s); c.id=uid('s'); c.x=r2(s.x+20); c.y=r2(s.y+20);
    m.shapes.push(c); added.push(c.id);
  }
  clearSel(); added.forEach(i=>sel.shapes.add(i)); commit();
}
function nudge(dx,dy){
  const m=model(); if(!selCount())return; push();
  for(const id of sel.shapes){const s=m.shapes.find(x=>x.id===id);
    if(s){s.x=r2(s.x+dx);s.y=r2(s.y+dy);}}
  for(const id of sel.labels){const l=m.labels.find(x=>x.id===id);
    if(l){l.x=r2(l.x+dx);l.y=r2(l.y+dy);}}
  for(const id of sel.edges){const e=m.edges.find(x=>x.id===id);
    if(e)e.points=e.points.map(p=>[r2(p[0]+dx),r2(p[1]+dy)]);}
  syncEdges(m,[...sel.shapes],{delta:[dx,dy],skip:[...sel.edges]}); commit();
}
function fitShape(id){
  const m=model(), s=m.shapes.find(x=>x.id===id); if(!s)return;
  const g=sizeFor(s.kind,s.text,m.maxChars);
  const cx=s.x+s.w/2;
  s.x=r2(cx-g.w/2); s.w=g.w; s.h=g.h; syncEdges(m,[s.id]);
}

/* ---------- инспектор ---------- */
function inspect(){
  const box=$('#inspBody'), m=model();
  if(sel.shapes.size===1&&!sel.edges.size){
    const s=m.shapes.find(x=>x.id===[...sel.shapes][0]);
    if(!s){box.innerHTML='';return;}
    box.innerHTML=
      `<label>${t('i_type')}</label><select id="fKind">${KINDS.map(k=>
        `<option value="${k}"${k===s.kind?' selected':''}>${KIND_LABEL(k)}</option>`).join('')}</select>`+
      `<label>${t('i_text')}</label><textarea id="fText" spellcheck="false">${esc(s.text)}</textarea>`+
      `<label style="display:flex;gap:7px;align-items:center;margin-top:11px">
        <input type="checkbox" id="fShift" style="width:auto" checked>
        ${t('i_shift')}</label>`+
      `<div class="row"><button class="primary" id="fApply">${t('i_apply')}</button>`+
      `<button id="fFit">${t('i_fit')}</button></div>`+
      `<div class="row"><button id="fDup">${t('i_dup')}</button>`+
      `<button id="fDel">${t('i_del')}</button></div>`+
      `<div class="row"><button id="fReroute">${t('i_reroute')}</button></div>`+
      `<p class="note">${t('i_hint_block')}</p>`;
    const apply=()=>{push();
      const shift=$('#fShift').checked, bottom=s.y+s.h, h0=s.h;
      s.kind=$('#fKind').value; s.text=$('#fText').value;
      fitShape(s.id);
      if(shift)shiftBelow(model(),bottom,r2(s.h-h0));
      syncEdges(model(),[s.id]);
      commit();const f=$('#fText');if(f)f.focus();};
    $('#fApply').onclick=apply; $('#fKind').onchange=apply;
    $('#fText').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();apply();}};
    $('#fFit').onclick=()=>{push();fitShape(s.id);commit();};
    $('#fReroute').onclick=()=>{push();
      const ok=id=>m.shapes.some(x=>x.id===id);
      const list=m.edges.filter(e=>e.from&&e.to&&ok(e.from.id)&&ok(e.to.id)&&
        (e.from.id===s.id||e.to.id===s.id));
      routeEdges(m,list,{free:true});     // вместе: идущие рядом линии разойдутся
      commit();toast(list.length?t('s_rerouted',list.length):t('s_no_links'));};
    $('#fDup').onclick=dupSel; $('#fDel').onclick=delSel;
    return;
  }
  if(sel.edges.size===1&&!sel.shapes.size){
    const e=m.edges.find(x=>x.id===[...sel.edges][0]);
    if(!e){box.innerHTML='';return;}
    const nm=r=>r?(m.shapes.find(s=>s.id===r.id)||{}).text||'—':t('i_free');
    box.innerHTML=
      `<p class="note">${t('i_from')}: <b>${esc(nm(e.from))}</b><br>${t('i_to')}: <b>${esc(nm(e.to))}</b></p>`+
      `<label>${t('i_arrow')}</label>
       <select id="fArrow"><option value="1"${e.arrow!==false?' selected':''}>${t('i_arrow_on')}</option>
       <option value="0"${e.arrow===false?' selected':''}>${t('i_arrow_off')}</option></select>`+
      `<div class="row"><button id="fStraight">${t('i_straight')}</button>
       <button id="fRoute">${t('i_route')}</button></div>`+
      `<div class="row"><button id="fDel">${t('i_del')}</button></div>`+
      `<p class="note">${t('i_hint_edge')}</p>`;
    $('#fArrow').onchange=()=>{push();e.arrow=$('#fArrow').value==='1';commit();};
    $('#fStraight').onclick=()=>{push();
      const a=e.points[0],b=e.points[e.points.length-1];
      e.points=Math.abs(a[0]-b[0])<2||Math.abs(a[1]-b[1])<2?[a,b]
        :[a,[a[0],r2((a[1]+b[1])/2)],[b[0],r2((a[1]+b[1])/2)],b];
      commit();};
    $('#fRoute').onclick=()=>{push();
      if(!rerouteEdge(m,e))toast(t('s_unbound'));
      commit();};
    $('#fDel').onclick=delSel;
    return;
  }
  if(sel.labels.size===1&&!sel.shapes.size&&!sel.edges.size){
    const l=m.labels.find(x=>x.id===[...sel.labels][0]);
    if(!l){box.innerHTML='';return;}
    box.innerHTML=`<label>${t('i_label_text')}</label>
      <input id="fText" value="${esc(l.text)}">
      <label>${t('i_align')}</label>
      <select id="fAn">${['start','middle','end'].map(a=>
        `<option value="${a}"${a===l.anchor?' selected':''}>${
          {start:t('i_left'),middle:t('i_center'),end:t('i_right')}[a]}</option>`).join('')}</select>
      <div class="row"><button class="primary" id="fApply">${t('i_apply')}</button>
      <button id="fDel">${t('i_del')}</button></div>`;
    const ap=()=>{push();l.text=$('#fText').value;l.anchor=$('#fAn').value;commit();};
    $('#fApply').onclick=ap; $('#fAn').onchange=ap;
    $('#fText').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();ap();}};
    $('#fDel').onclick=delSel;
    return;
  }
  if(selCount()>1){
    box.innerHTML=`<p class="note">${t('i_selected',selCount())}</p>
      <div class="row"><button id="fDel">${t('i_del')}</button>
      <button id="fDup">${t('i_dup')}</button></div>
      <label>${t('i_align_v')}</label>
      <div class="row"><button id="fAlign">${t('i_align_c')}</button>
      <button id="fSpread">${t('i_spread')}</button></div>`;
    $('#fDel').onclick=delSel; $('#fDup').onclick=dupSel;
    $('#fAlign').onclick=()=>{const m2=model();const ss=m2.shapes.filter(s=>sel.shapes.has(s.id));
      if(ss.length<2)return;push();
      const cx=ss.reduce((a,s)=>a+s.x+s.w/2,0)/ss.length;
      ss.forEach(s=>s.x=r2(cx-s.w/2)); syncEdges(m2,ss.map(s=>s.id)); commit();};
    $('#fSpread').onclick=()=>{const m2=model();
      const ss=m2.shapes.filter(s=>sel.shapes.has(s.id)).sort((a,b)=>a.y-b.y);
      if(ss.length<3)return;push();
      const top=ss[0].y, bot=ss[ss.length-1].y, step=(bot-top)/(ss.length-1);
      ss.forEach((s,i)=>s.y=r2(top+step*i)); syncEdges(m2,ss.map(s=>s.id)); commit();};
    return;
  }
  box.innerHTML=`<p class="note">${t('i_empty')}</p>`;
}

/* ---------- панель схем ---------- */
function buildTree(filter){
  const box=$('#tree'); box.innerHTML='';
  const q=(filter||'').trim().toLowerCase();
  let last=null;
  for(const it of entries()){
    if(q&&!(it.name.toLowerCase().includes(q)||it.rel.toLowerCase().includes(q)))continue;
    if(it.rel!==last){last=it.rel;
      const d=document.createElement('div');d.className='sec';d.textContent=it.rel;
      box.appendChild(d);}
    const a=document.createElement('a');
    a.innerHTML=`<span>${esc(nameOf(it))}</span><span class="ln">${
      it.custom?t('own'):':'+it.line}</span>`;
    if(isEdited(it.anchor))a.classList.add('edited');
    if(cur===it.anchor)a.classList.add('active');
    a.onclick=()=>show(it.anchor);
    box.appendChild(a);
  }
}
function show(anchor){
  cur=anchor; clearSel(); hist=[]; future=[]; view=null; pending=null;
  const it=meta();
  $('#figName').textContent=nameOf(it);
  $('#figMeta').textContent=it.signature+(it.line?('  ·  '+it.rel+':'+it.line):'');
  const i=entries().findIndex(x=>x.anchor===anchor);
  $('#caption').textContent=t('caption',i+1,nameOf(it));
  document.title=nameOf(it)+' — '+t('app_title',DATA.folder||'');
  ensureView(model(),true);
  draw(); buildTree($('#search').value); inspect();
}
function newDoc(){
  const name=prompt(t('m_new_name'),t('m_new_default',custom.length+1));
  if(!name)return;
  const anchor='custom_'+uid('d');
  custom.push({anchor,name});
  docs[anchor]=hydrate(emptyDoc(name));
  saveStore(); show(anchor); toast(t('s_new'));
}
function delDoc(){
  const it=meta(); if(!it)return;
  if(it.custom){
    if(!confirm(t('m_del_chart',nameOf(it))))return;
    custom=custom.filter(c=>c.anchor!==it.anchor); delete docs[it.anchor];
    saveStore(); show(entries()[0].anchor); toast(t('s_deleted'));
  }else{
    if(!dirty.has(it.anchor)){toast(t('s_no_edits'));return;}
    if(!confirm(t('m_reset_chart',nameOf(it))))return;
    delete docs[it.anchor]; dirty.delete(it.anchor);
    saveStore(); show(it.anchor); toast(t('s_reset'));
  }
}

/* ---------- тема, язык, имя схемы ---------- */
function applyTheme(){
  document.body.dataset.theme=THEME;
  const b=$('#btnTheme'); if(b)b.textContent=THEME==='dark'?'☀':'☾';
  if(cur)draw();
}
function toggleTheme(){THEME=THEME==='dark'?'light':'dark';saveStore();applyTheme();}

function applyLang(){
  document.documentElement.lang=LANG;
  const b=$('#btnLang'); if(b)b.textContent=LANG==='ru'?'EN':'RU';
  document.querySelectorAll('[data-i18n]').forEach(el=>{
    el.textContent=t(el.getAttribute('data-i18n'));});
  document.querySelectorAll('[data-i18n-title]').forEach(el=>{
    el.title=t(el.getAttribute('data-i18n-title'));});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{
    el.placeholder=t(el.getAttribute('data-i18n-ph'));});
  $('#appTitle').textContent=t('app_title',DATA.folder||'');
  $('#appSub').textContent=t('charts_count',DATA.items.length);
  if(cur){show(cur);}
}
function toggleLang(){LANG=LANG==='ru'?'en':'ru';saveStore();applyLang();}

function renameChart(){
  const it=meta(); if(!it||!cur)return;
  const name=prompt(t('m_rename'),nameOf(it));
  if(name===null)return;
  const clean=name.trim();
  if(!clean||clean===nameOf(it))return;
  names[cur]=clean;
  const own=custom.find(c=>c.anchor===cur);
  if(own)own.name=clean;
  saveStore(); show(cur); toast(t('s_renamed'));
}

/* ---------- инструменты ---------- */
function setTool(t){
  tool=t; pending=null;
  document.querySelectorAll('[data-tool]').forEach(b=>
    b.classList.toggle('on',b.getAttribute('data-tool')===t));
  const svg=$('#sheet svg');
  if(svg)svg.style.cursor=(t==='select')?'default':'crosshair';
  drawUI();
}

/* ---------- экспорт ---------- */
function exportSVG(){
  const it=meta();
  const title=exportTitle?(nameOf(it)+(it.line?' — '+it.rel:'')):null;
  return renderSVG(model(),{title,name:nameOf(it)}).svg;
}
function download(blob,name){
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;
  document.body.appendChild(a);a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},400);
}
function svgToPng(svgText,scale){
  return new Promise((res,rej)=>{
    const blob=new Blob([svgText],{type:'image/svg+xml;charset=utf-8'});
    const url=URL.createObjectURL(blob),img=new Image();
    img.onload=()=>{const c=document.createElement('canvas');
      c.width=Math.round(img.width*scale);c.height=Math.round(img.height*scale);
      const ctx=c.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,c.width,c.height);
      ctx.drawImage(img,0,0,c.width,c.height);URL.revokeObjectURL(url);
      c.toBlob(b=>b?res(b):rej(new Error('canvas')),'image/png');};
    img.onerror=e=>{URL.revokeObjectURL(url);rej(e);};
    img.src=url;});
}
async function doPng(copy){
  const scale=parseFloat($('#scale').value);
  try{
    const blob=await svgToPng(exportSVG(),scale);
    if(copy){await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);
      toast(t('s_copied'));}
    else{download(blob,fileBase()+'@'+scale+'x.png');toast(t('s_png'));}
  }catch(e){toast(t(copy?'s_clip_fail':'s_png_fail'));}
}
function exportProject(){
  download(new Blob([JSON.stringify({docs,custom,names},null,1)],
    {type:'application/json'}),'blockwright-project.json');
  toast(t('s_proj_saved'));
}
function importProject(file){
  const rd=new FileReader();
  rd.onload=()=>{try{
      const d=JSON.parse(rd.result);
      docs=Object.assign(docs,d.docs||{});
      const have=new Set(custom.map(c=>c.anchor));
      for(const c of (d.custom||[]))if(!have.has(c.anchor))custom.push(c);
      names=Object.assign(names,d.names||{});
      saveStore(); show(cur||entries()[0].anchor); toast(t('s_proj_loaded'));
    }catch(e){toast(t('s_proj_bad'));}};
  rd.readAsText(file);
}

/* ---------- запуск ---------- */
window.addEventListener('DOMContentLoaded',()=>{
  loadRouter();              // в фоне: до загрузки линии ведёт запасной алгоритм
  loadStore();
  applyTheme();
  applyLang();
  const hash=decodeURIComponent(location.hash.slice(1));
  const list=entries();
  show(list.find(i=>i.anchor===hash)?hash:list[0].anchor);
  $('#search').oninput=e=>buildTree(e.target.value);
  $('#btnNew').onclick=newDoc;
  $('#btnDel').onclick=delDoc;
  $('#btnTheme').onclick=toggleTheme;
  $('#btnLang').onclick=toggleLang;
  $('#btnRename').onclick=renameChart;
  $('#figName').ondblclick=renameChart;
  const cap=$('#capTitle');
  cap.checked=exportTitle;
  cap.onchange=()=>{exportTitle=cap.checked;saveStore();};
  $('#btnMenu').onclick=()=>document.body.classList.toggle('nav-open');
  $('#tree').addEventListener('click',()=>document.body.classList.remove('nav-open'));
  document.querySelectorAll('[data-tool]').forEach(b=>
    b.onclick=()=>setTool(b.getAttribute('data-tool')));
  $('#zoomIn').onclick=()=>{zoom=Math.min(3,zoom*1.25);draw();};
  $('#zoomOut').onclick=()=>{zoom=Math.max(.2,zoom/1.25);draw();};
  $('#zoom100').onclick=()=>{zoom=1;draw();};
  $('#zoomFit').onclick=()=>{ensureView(model(),true);
    const out=renderSVG(model(),{view});
    zoom=Math.max(.2,Math.min(2,($('#stage').clientWidth-80)/out.w));draw();};
  $('#btnUndo').onclick=undo; $('#btnRedo').onclick=redo;
  $('#btnSvg').onclick=()=>{download(new Blob([exportSVG()],
    {type:'image/svg+xml;charset=utf-8'}),fileBase()+'.svg');
    toast(t('s_svg'));};
  $('#btnPng').onclick=()=>doPng(false);
  $('#btnCopy').onclick=()=>doPng(true);
  $('#btnPrint').onclick=()=>window.print();
  $('#btnSave').onclick=exportProject;
  $('#btnLoad').onclick=()=>$('#fileIn').click();
  $('#fileIn').onchange=e=>{if(e.target.files[0])importProject(e.target.files[0]);
    e.target.value='';};
  document.addEventListener('keydown',ev=>{
    const tag=(ev.target.tagName||'').toLowerCase();
    if(tag==='input'||tag==='textarea'||tag==='select')return;
    const ctrl=ev.ctrlKey||ev.metaKey;
    if(ctrl&&ev.key.toLowerCase()==='z'){ev.preventDefault();ev.shiftKey?redo():undo();return;}
    if(ctrl&&ev.key.toLowerCase()==='y'){ev.preventDefault();redo();return;}
    if(ctrl&&ev.key.toLowerCase()==='d'){ev.preventDefault();dupSel();return;}
    if(ctrl&&ev.key.toLowerCase()==='a'){ev.preventDefault();const m=model();
      m.shapes.forEach(s=>sel.shapes.add(s.id));m.edges.forEach(e=>sel.edges.add(e.id));
      m.labels.forEach(l=>sel.labels.add(l.id));drawUI();inspect();return;}
    if(ev.key==='Delete'||ev.key==='Backspace'){ev.preventDefault();delSel();return;}
    if(ev.key==='Escape'){clearSel();setTool('select');drawUI();inspect();return;}
    const step=ev.shiftKey?10:1;
    if(ev.key==='ArrowLeft'){ev.preventDefault();nudge(-step,0);}
    if(ev.key==='ArrowRight'){ev.preventDefault();nudge(step,0);}
    if(ev.key==='ArrowUp'){ev.preventDefault();nudge(0,-step);}
    if(ev.key==='ArrowDown'){ev.preventDefault();nudge(0,step);}
    if(ev.key==='v')setTool('select');
    if(ev.key==='c')setTool('connect');
    if(ev.key==='t')setTool('label');
    const idx='1234567'.indexOf(ev.key);
    if(idx>=0)setTool('add:'+KINDS[idx]);
  });
  $('#stage').addEventListener('wheel',ev=>{
    if(!ev.ctrlKey)return; ev.preventDefault();
    zoom=Math.max(.2,Math.min(3,zoom*(ev.deltaY<0?1.1:1/1.1)));draw();
  },{passive:false});
});
"""

ICONS = {
    "terminator": '<rect x="3" y="7" width="20" height="12" rx="6"/>',
    "process": '<rect x="3" y="7" width="20" height="12"/>',
    "io": '<polygon points="7,7 23,7 19,19 3,19"/>',
    "decision": '<polygon points="13,5 23,13 13,21 3,13"/>',
    "predefined": '<rect x="3" y="7" width="20" height="12"/>'
                  '<line x1="7" y1="7" x2="7" y2="19"/><line x1="19" y1="7" x2="19" y2="19"/>',
    "preparation": '<polygon points="7,7 19,7 23,13 19,19 7,19 3,13"/>',
    "connector": '<circle cx="13" cy="13" r="7"/>',
}
KINDS = ("terminator", "process", "io", "decision", "predefined",
         "preparation", "connector")


def _palette():
    """Кнопки палитры; подписи проставляет applyLang() по data-i18n-title."""
    ico = ('<svg width="26" height="26" viewBox="0 0 26 26" fill="none" '
           'stroke="currentColor" stroke-width="1.6">')
    out = [f'<button data-tool="select" class="on" data-i18n-title="t_select">{ico}'
           '<path d="M7 4 L7 20 L11 16 L14 22 L16 21 L13 15 L19 15 Z" '
           'fill="var(--panel)"/></svg></button>',
           f'<button data-tool="connect" data-i18n-title="t_connect">{ico}'
           '<path d="M5 6 H15 V19"/><path d="M12 16 L15 20 L18 16 Z" '
           'fill="currentColor"/></svg></button>',
           f'<button data-tool="label" data-i18n-title="t_label">{ico}'
           '<path d="M6 8 H20 M13 8 V19" stroke-width="1.8"/></svg></button>',
           '<div class="gap"></div>']
    for kind in KINDS:
        out.append(f'<button data-tool="add:{kind}" data-i18n-title="t_{kind}">'
                   f'<svg width="26" height="26" viewBox="0 0 26 26" fill="var(--panel)" '
                   f'stroke="currentColor" stroke-width="1.6">{ICONS[kind]}</svg></button>')
    return "".join(out)


def _router_scripts():
    """libavoid из vendor/web, встроенный прямо в страницу.

    WebAssembly кладётся строкой base64: fetch() со страницы, открытой как
    file://, браузеры запрещают, а так альбом остаётся одним файлом, который
    работает офлайн где угодно. Нет файлов — редактор обойдётся без них.
    """
    js_path = web_asset("libavoid", "libavoid.js")
    wasm_path = web_asset("libavoid", "libavoid.wasm")
    if not (js_path and wasm_path):
        return ""
    with open(js_path, encoding="utf-8") as fh:
        js = fh.read().replace("</", "<\\/")
    with open(wasm_path, "rb") as fh:
        wasm = base64.b64encode(fh.read()).decode("ascii")
    return (f"<script>{js}</script>\n"
            f'<script>const AVOID_WASM="{wasm}";</script>\n')


def render_html(entries, title="Блок-схемы", folder="", lang="ru", theme="light"):
    """entries: список dict(rel, name, signature, line, anchor, model)."""
    payload = json.dumps({"folder": folder or title, "items": entries,
                          "lang": lang, "theme": theme},
                         ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{xml_escape(title)}</title>
<style>{CSS}</style></head>
<body data-theme="{theme}">
<div class="topbar">
  <button id="btnMenu" class="only-narrow" data-i18n-title="b_menu_t">☰</button>
  <div class="brand"><span id="appTitle">{xml_escape(title)}</span>
    <span class="sub"> · <span id="appSub"></span></span></div>
  <div class="grow"></div>
  <div class="group">
    <button id="btnUndo" data-i18n-title="b_undo">↶</button>
    <button id="btnRedo" data-i18n-title="b_redo">↷</button>
  </div>
  <div class="sep"></div>
  <div class="group">
    <label class="check" data-i18n-title="cap_title_t">
      <input type="checkbox" id="capTitle" checked>
      <span data-i18n="cap_title"></span></label>
    <select id="scale" title="PNG">
      <option value="1">PNG ×1</option><option value="2" selected>PNG ×2</option>
      <option value="3">PNG ×3</option><option value="4">PNG ×4</option>
    </select>
    <button id="btnCopy" class="primary" data-i18n="b_copy" data-i18n-title="b_copy_t"></button>
    <button id="btnPng" data-i18n="b_png"></button>
    <button id="btnSvg" data-i18n="b_svg" data-i18n-title="b_svg_t"></button>
    <button id="btnPrint" class="wide" data-i18n="b_print"></button>
  </div>
  <div class="sep"></div>
  <div class="group">
    <button id="btnSave" class="wide" data-i18n="b_project" data-i18n-title="b_project_t"></button>
    <button id="btnLoad" class="wide" data-i18n="b_open" data-i18n-title="b_open_t"></button>
    <input id="fileIn" type="file" accept=".json,application/json" hidden>
    <button id="btnTheme" data-i18n-title="b_theme_t">☾</button>
    <button id="btnLang" data-i18n-title="b_lang_t">EN</button>
  </div>
</div>

<div class="layout">
  <aside class="nav">
    <div class="navhead">
      <input id="search" type="search" data-i18n-ph="search">
      <button id="btnNew" data-i18n-title="b_new_t">＋</button>
    </div>
    <div class="tree" id="tree"></div>
    <div class="navfoot">
      <button id="btnDel" class="ghost danger" data-i18n="b_del" data-i18n-title="b_del_t"></button>
    </div>
  </aside>

  <main>
    <div class="toolbar">
      <span class="name" id="figName" data-i18n-title="b_rename_t"></span>
      <button id="btnRename" class="ghost tiny" data-i18n-title="b_rename_t">✎</button>
      <span class="meta" id="figMeta"></span>
      <div class="grow"></div>
      <div class="group">
        <button id="zoomOut" data-i18n-title="z_out">−</button>
        <span class="zoomval" id="zoomVal">100%</span>
        <button id="zoomIn" data-i18n-title="z_in">+</button>
        <button id="zoom100">1:1</button>
        <button id="zoomFit" class="wide" data-i18n="z_fit"></button>
      </div>
    </div>
    <div class="work">
      <div class="palette">{_palette()}</div>
      <div class="stage" id="stage">
        <div class="sheet" id="sheet"></div>
        <div class="caption" id="caption"></div>
      </div>
    </div>
  </main>

  <aside class="insp">
    <h3 data-i18n="props"></h3>
    <div id="inspBody"></div>
  </aside>
</div>
<div class="toast" id="toast"></div>
<script>const DATA={payload};</script>
{_router_scripts()}<script>{JS_CORE}{JS_APP}</script>
</body></html>
"""
