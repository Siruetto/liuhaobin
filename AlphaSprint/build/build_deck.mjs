import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";


const workspaceDir = "C:\\Users\\Sirue'tto\\Desktop\\软件工程\\liuhaobin\\AlphaSprint";
const assetsDir = path.join(workspaceDir, "assets");
const buildDir = path.join(workspaceDir, "build", "deck");
const previewDir = path.join(buildDir, "previews");
const finalDir = path.join(workspaceDir, "PPT");
const finalPath = path.join(finalDir, "报时鸟-Alpha冲刺答辩.pptx");
const skillDir =
  "C:\\Users\\Sirue'tto\\.codex\\plugins\\cache\\openai-primary-runtime\\presentations\\26.1116.12020\\skills\\presentations";
const nodeModules =
  "C:\\Program Files\\WindowsApps\\OpenAI.CodexPrimaryRuntime.v26-1116-1220-0_26.1116.1220.0_x64__3k8sg7r9htsxt\\dependencies\\node\\node_modules";
const artifactToolPath = path.join(
  nodeModules,
  "@oai",
  "artifact-tool",
  "dist",
  "artifact_tool.mjs",
);

const { Presentation, PresentationFile } = await import(
  pathToFileURL(artifactToolPath).href
);
const { finalizePresentation } = await import(
  pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href
);

const C = {
  ink: "#17201D",
  inkSoft: "#52605A",
  paper: "#F4EFE6",
  card: "#FFFDF8",
  line: "#DED7CA",
  orange: "#F26A2E",
  orangeDark: "#D9511C",
  teal: "#2D6F63",
  tealPale: "#E2F1EB",
  sand: "#E9E0D2",
  white: "#FFFFFF",
};
const FONT = "Noto Sans SC";

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(finalDir, { recursive: true });

function addText(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.name = options.name || "text";
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize || "16pt",
    bold: options.bold || false,
    color: options.color || C.ink,
    alignment: options.alignment || "left",
    verticalAlignment: options.verticalAlignment || "top",
    autoFit: "none",
    insets: options.insets ?? 0,
    lineSpacing: options.lineSpacing ?? 1.05,
  };
  return shape;
}

function addRule(slide, left, top, width, color = C.line, height = 1) {
  return slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height },
    fill: color,
    line: { style: "solid", fill: "none", width: 0 },
  });
}

function addBaseSlide(presentation, number, section, title, subtitle = "") {
  const slide = presentation.slides.add();
  slide.background.fill = C.paper;
  addText(slide, section.toUpperCase(), { left: 64, top: 28, width: 520, height: 24 }, {
    fontSize: "10pt",
    bold: true,
    color: C.orangeDark,
  });
  addText(slide, title, { left: 64, top: 60, width: 1150, height: 72 }, {
    fontSize: "30pt",
    bold: true,
    color: C.ink,
  });
  if (subtitle) {
    addText(slide, subtitle, { left: 66, top: 132, width: 1110, height: 38 }, {
      fontSize: "12.5pt",
      color: C.inkSoft,
    });
  }
  addText(slide, String(number).padStart(2, "0"), { left: 1192, top: 676, width: 34, height: 20 }, {
    fontSize: "9pt",
    color: C.inkSoft,
    alignment: "right",
  });
  addRule(slide, 64, 686, 1118, C.line);
  return slide;
}

function addCard(slide, left, top, width, height, fill = C.card, stroke = C.line) {
  return slide.shapes.add({
    geometry: "roundRect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: stroke, width: 1 },
    borderRadius: "rounded-2xl",
  });
}

function styleTable(table, headerFill = C.ink, bodyColor = C.ink, headerColor = C.white) {
  table.styleOptions = { headerRow: true, bandedRows: false, firstColumn: false };
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  const rows = table.rows.length;
  const columns = table.columns.length;
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const cell = table.getCell(row, column);
      cell.fill = row === 0 ? headerFill : C.card;
      cell.text.style = {
        typeface: FONT,
        fontSize: "10.5pt",
        bold: row === 0 || row === rows - 1,
        color: row === 0 ? headerColor : bodyColor,
        verticalAlignment: "middle",
        insets: { top: 8, right: 10, bottom: 8, left: 10 },
      };
    }
  }
}

function addMetric(slide, x, y, value, label, color = C.orangeDark) {
  addText(slide, value, { left: x, top: y, width: 160, height: 58 }, {
    fontSize: "32pt",
    bold: true,
    color,
  });
  addText(slide, label, { left: x, top: y + 58, width: 180, height: 34 }, {
    fontSize: "10.5pt",
    color: C.inkSoft,
  });
}

async function addPng(slide, filename, position, alt) {
  const file = await fs.readFile(path.join(assetsDir, filename));
  const bytes = file.buffer.slice(file.byteOffset, file.byteOffset + file.byteLength);
  slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt,
    fit: "cover",
    position,
    geometry: "roundRect",
    borderRadius: "rounded-xl",
  });
}

const presentation = Presentation.create({
  slideSize: { width: 1280, height: 720 },
});
presentation.slides.keep([]);

// 01 Cover
{
  const slide = presentation.slides.add();
  slide.background.fill = C.ink;
  slide.shapes.add({
    geometry: "rect",
    position: { left: 944, top: 0, width: 336, height: 720 },
    fill: C.orange,
    line: { style: "solid", fill: "none", width: 0 },
  });
  addText(slide, "DESK BIRD", { left: 72, top: 56, width: 400, height: 28 }, {
    fontSize: "11pt",
    bold: true,
    color: "#FFB68E",
  });
  addText(slide, "报时鸟", { left: 72, top: 168, width: 790, height: 100 }, {
    fontSize: "56pt",
    bold: true,
    color: C.white,
  });
  addText(slide, "Alpha 冲刺总结", { left: 76, top: 270, width: 790, height: 62 }, {
    fontSize: "28pt",
    bold: true,
    color: "#FFD4BE",
  });
  addText(
    slide,
    "说一句就记，到点主动开口。\n把设计原型推进到可运行、可测试、可演示的产品。",
    { left: 76, top: 360, width: 740, height: 108 },
    { fontSize: "18pt", color: "#E7EEEB", lineSpacing: 1.3 },
  );
  addText(
    slide,
    "报时鸟团队 · 7 人\n2026-11-23 至 2026-12-06",
    { left: 76, top: 590, width: 600, height: 56 },
    { fontSize: "12pt", color: "#B7C5C0", lineSpacing: 1.3 },
  );
  slide.speakerNotes.text =
    "封面。开场用一句话说明这次 Alpha 冲刺的目标：把原型变成真正能执行的产品。";
}

// 02 Product result
{
  const slide = addBaseSlide(
    presentation,
    2,
    "01 / Alpha outcome",
    "设计已经变成一条真实可执行的提醒链路",
    "用户说一句话，系统完成解析、入库，并在到点时主动弹出和播报。",
  );
  addText(slide, "01", { left: 66, top: 208, width: 42, height: 30 }, {
    fontSize: "14pt",
    bold: true,
    color: C.orange,
  });
  addText(slide, "自然语言新增提醒", { left: 112, top: 204, width: 430, height: 40 }, {
    fontSize: "18pt",
    bold: true,
  });
  addText(slide, "支持 one-time / daily / interval，时间与内容一次说完。", {
    left: 112,
    top: 244,
    width: 450,
    height: 38,
  }, { fontSize: "12.5pt", color: C.inkSoft });
  addText(slide, "02", { left: 66, top: 318, width: 42, height: 30 }, {
    fontSize: "14pt",
    bold: true,
    color: C.orange,
  });
  addText(slide, "真实动作与持久化", { left: 112, top: 314, width: 430, height: 40 }, {
    fontSize: "18pt",
    bold: true,
  });
  addText(slide, "原 9 个工具 + 课表查询；提醒写入 SQLite，重启不丢。", {
    left: 112,
    top: 354,
    width: 450,
    height: 38,
  }, { fontSize: "12.5pt", color: C.inkSoft });
  addText(slide, "03", { left: 66, top: 428, width: 42, height: 30 }, {
    fontSize: "14pt",
    bold: true,
    color: C.orange,
  });
  addText(slide, "到点主动开口", { left: 112, top: 424, width: 430, height: 40 }, {
    fontSize: "18pt",
    bold: true,
  });
  addText(slide, "页面气泡 + 语音播报；失败后仍保留文字输入。", {
    left: 112,
    top: 464,
    width: 450,
    height: 38,
  }, { fontSize: "12.5pt", color: C.inkSoft });
  await addPng(slide, "01-对话与提醒.png", {
    left: 612,
    top: 178,
    width: 560,
    height: 350,
  }, "报时鸟真实网页：对话与提醒面板");
  addText(slide, "真实网页截图 · 1440 × 900", { left: 612, top: 540, width: 560, height: 24 }, {
    fontSize: "9.5pt",
    color: C.inkSoft,
    alignment: "right",
  });
  addMetric(slide, 66, 574, "26", "自动化测试通过", C.teal);
  addMetric(slide, 260, 574, "10", "工具保持稳定", C.teal);
  addMetric(slide, 454, 574, "0", "第三方运行依赖", C.teal);
  slide.speakerNotes.text =
    "这一页只讲结果：产品已经不是静态原型。强调 26 个测试和 10 个工具硬口径。";
}

// 03 Sprint objective and previous reflection
{
  const slide = addBaseSlide(
    presentation,
    3,
    "02 / Reflection",
    "冲刺前最需要改的是“看起来能做”和“真的能做”的落差",
    "前两次团队作业完成了需求、UML、数据库和墨刀原型，但核心动作仍需要真实后端证据。",
  );
  const columns = [
    ["旧状态", "需求、线框图和交互说明齐全", "问题是静态状态无法证明提醒真的入库、真的触发。"],
    ["改进判断", "先完成核心闭环，再接语音和硬件", "把评测需要的 5 秒触发、断网可用和安全分支先做稳。"],
    ["工程标准", "每个功能必须有测试或复现路径", "不能靠演示者解释，验收者要能自己运行。"],
  ];
  columns.forEach(([label, headline, detail], index) => {
    const x = 66 + index * 374;
    addCard(slide, x, 208, 350, 344, index === 1 ? "#FFF4EC" : C.card, index === 1 ? C.orange : C.line);
    addText(slide, label, { left: x + 24, top: 232, width: 300, height: 24 }, {
      fontSize: "10pt",
      bold: true,
      color: index === 1 ? C.orangeDark : C.teal,
    });
    addText(slide, headline, { left: x + 24, top: 282, width: 294, height: 104 }, {
      fontSize: "19pt",
      bold: true,
      lineSpacing: 1.2,
    });
    addRule(slide, x + 24, 408, 302, C.line);
    addText(slide, detail, { left: x + 24, top: 432, width: 294, height: 92 }, {
      fontSize: "12pt",
      color: C.inkSoft,
      lineSpacing: 1.3,
    });
  });
  addText(slide, "冲刺原则：先闭环，后加分；先证据，后表述。", {
    left: 66,
    top: 584,
    width: 1118,
    height: 42,
  }, { fontSize: "18pt", bold: true, color: C.orangeDark, alignment: "center" });
  slide.speakerNotes.text =
    "总结前序工作。不要把设计文档说成产品完成，直接讲这次冲刺修正的地方。";
}

// 04 Team division and workload
{
  const slide = addBaseSlide(
    presentation,
    4,
    "03 / Team",
    "7 人分工覆盖架构、前端、测试、部署与演示",
    "右侧是冲刺计划权重，左侧 Day 1 实际占比只记录已经发生的工作；Day 14 将按真实证据更新。",
  );
  const rows = [
    ["成员", "角色", "负责内容", "计划权重(百分点)", "Day 1 实际(百分点)"],
    ["刘浩彬", "架构 / 后端", "Agent、Planner、Scheduler、API、测试", "28", "100"],
    ["李彦峰", "后端 / 运维", "数据库、部署、设备接口、回归", "14", "0"],
    ["段旷卓", "前端", "主界面、交互、语音、提醒气泡", "14", "0"],
    ["曲浩宾", "前端 / 文档", "视觉规范、原型落地、博客统稿", "12", "0"],
    ["邓家俊", "PM / 测试", "验收矩阵、异常测试、风险跟踪", "12", "0"],
    ["李忠林", "测试 / 演示", "端到端执行、录屏、Vlog、答辩", "10", "0"],
    ["刘俊宁", "测试 / 文档", "数据、校对、截图、发布检查", "10", "0"],
    ["合计", "", "", "100", "100"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 5,
    left: 66,
    top: 194,
    width: 1118,
    height: 450,
    columnWidths: [126, 150, 520, 150, 172],
    values: rows,
  });
  styleTable(table);
  table.rows[0].height = 44;
  for (let row = 1; row < rows.length; row += 1) {
    table.rows[row].height = row === rows.length - 1 ? 40 : 50;
  }
  addText(slide, "注：计划权重已合计 100%；实际工作量必须由每日日志与工时表最终核算。", {
    left: 70,
    top: 650,
    width: 990,
    height: 24,
  }, { fontSize: "9.5pt", color: C.inkSoft });
  slide.speakerNotes.text =
    "分工与工作量页。明确当前实际只有 Day 1，计划权重不等于实际工时。";
}

// 05 14-day plan
{
  const slide = addBaseSlide(
    presentation,
    5,
    "04 / Plan",
    "14 天按四个阶段推进，关键训练点提前到前半程",
    "站立会每天 10 分钟；Day 7 和 Day 10 设置完整回归，避免最后一天集中联调。",
  );
  const rows = [
    ["阶段", "日期", "核心任务", "里程碑"],
    ["Day 1-3", "11.23-11.25", "提醒闭环、API、记忆与异常", "核心链路可运行"],
    ["Day 4-6", "11.26-11.28", "语音、主动播报、后台视图", "可完整演示"],
    ["Day 7-10", "11.29-12.02", "中期评审、安全、响应式、A1-A8", "端到端回归"],
    ["Day 11-14", "12.03-12.06", "硬件、部署、Vlog、总结、Release", "Alpha 发布"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 4,
    left: 66,
    top: 192,
    width: 1118,
    height: 288,
    columnWidths: [160, 214, 454, 290],
    values: rows,
  });
  styleTable(table);
  table.rows[0].height = 44;
  for (let row = 1; row < rows.length; row += 1) table.rows[row].height = 61;
  const milestones = [
    ["Day 1", "10 工具 + 26 测试", C.orange],
    ["Day 7", "中期回归", C.teal],
    ["Day 10", "A1-A8 验收", C.teal],
    ["Day 14", "v0.1.0-alpha.1", C.orange],
  ];
  milestones.forEach(([day, label, color], index) => {
    const x = 82 + index * 288;
    addText(slide, day, { left: x, top: 526, width: 76, height: 24 }, {
      fontSize: "10pt",
      bold: true,
      color,
    });
    addText(slide, label, { left: x + 66, top: 524, width: 205, height: 28 }, {
      fontSize: "13pt",
      bold: true,
    });
  });
  slide.speakerNotes.text =
    "预期计划。强调不是平均排期，而是把风险高的语音和回归提前。";
}

// 06 Burndown through Day 1
{
  const slide = addBaseSlide(
    presentation,
    6,
    "05 / Progress",
    "Day 1 已从 80 点降到 54 点，但实际曲线只能记录到今天",
    "图表是可编辑的原生图表。Day 2-14 的点必须在每日冲刺结束后由日志数据更新。",
  );
  slide.charts.add("line", {
    position: { left: 78, top: 190, width: 760, height: 430 },
    categories: ["Day 0", "Day 1"],
    series: [
      {
        name: "计划剩余",
        values: [80, 54],
        line: { style: "solid", fill: C.teal, width: 3 },
      },
      {
        name: "实际剩余",
        values: [80, 54],
        line: { style: "solid", fill: C.orange, width: 3 },
      },
    ],
    title: "实际燃尽进度（截至 Day 1）",
    titleTextStyle: { typeface: FONT, fontSize: 14, bold: true, color: C.ink },
    legend: { position: "bottom", overlay: false },
    yAxis: {
      title: { text: "剩余故事点" },
      majorGridlines: { style: "solid", fill: C.line, width: 1 },
      min: 0,
      max: 90,
    },
    xAxis: { title: { text: "冲刺日" } },
    textStyle: { typeface: FONT, color: C.inkSoft, fontSize: 11 },
  });
  addCard(slide, 878, 206, 306, 170, "#FFF4EC", C.orange);
  addText(slide, "26", { left: 906, top: 230, width: 120, height: 70 }, {
    fontSize: "44pt",
    bold: true,
    color: C.orangeDark,
  });
  addText(slide, "Day 1 完成故事点", { left: 908, top: 304, width: 220, height: 28 }, {
    fontSize: "12pt",
    color: C.inkSoft,
  });
  addText(slide, "54 / 80", { left: 908, top: 340, width: 220, height: 28 }, {
    fontSize: "18pt",
    bold: true,
  });
  addCard(slide, 878, 400, 306, 156, C.card, C.line);
  addText(slide, "最终更新要求", { left: 902, top: 424, width: 240, height: 26 }, {
    fontSize: "11pt",
    bold: true,
    color: C.teal,
  });
  addText(slide, "Day 14 前补齐 14 个实际点，并把冲刺日志链接放入备注与总结。", {
    left: 902,
    top: 462,
    width: 250,
    height: 72,
  }, { fontSize: "11.5pt", color: C.inkSoft, lineSpacing: 1.25 });
  slide.speakerNotes.text =
    "进度页。今天只展示实际发生的 Day 1，不把计划值伪装成实际值。";
}

// 07 Demo screenshot
{
  const slide = addBaseSlide(
    presentation,
    7,
    "06 / Demo",
    "到点提醒闭环：看得见、听得到、能继续处理",
    "到点后用户可以看到提醒内容，也能完成或推迟；浏览器不支持语音时仍然保留文字提示。",
  );
  await addPng(slide, "05-主动提醒弹窗.png", {
    left: 66,
    top: 186,
    width: 760,
    height: 450,
  }, "报时鸟主动提醒弹窗");
  const steps = [
    ["1", "到点事件", "后台值守线程扫描 SQLite"],
    ["2", "主动弹出", "右下角提醒气泡置顶"],
    ["3", "语音播报", "调用浏览器 TTS"],
    ["4", "用户动作", "完成或 10 分钟后再提醒"],
  ];
  steps.forEach(([number, headline, detail], index) => {
    const y = 198 + index * 102;
    addText(slide, number, { left: 866, top: y, width: 36, height: 34 }, {
      fontSize: "14pt",
      bold: true,
      color: C.orangeDark,
    });
    addText(slide, headline, { left: 908, top: y - 2, width: 240, height: 28 }, {
      fontSize: "16pt",
      bold: true,
    });
    addText(slide, detail, { left: 908, top: y + 28, width: 240, height: 42 }, {
      fontSize: "10.5pt",
      color: C.inkSoft,
    });
  });
  addText(slide, "现场演示：对话新增提醒 → 等 3 秒 → 主动弹窗", {
    left: 66,
    top: 650,
    width: 760,
    height: 24,
  }, { fontSize: "10pt", bold: true, color: C.teal });
  slide.speakerNotes.text =
    "作品演示页。如果现场麦克风不可用，直接打字；主动提醒通过演示按钮或 API 触发。";
}

// 08 Architecture diagram
{
  const slide = addBaseSlide(
    presentation,
    8,
    "07 / Architecture",
    "实际架构：复用四个模块，新增调度与浏览器语音",
    "服务端只使用 Python 3.8+ 标准库；前端使用原生 HTML/CSS/JS，没有第三方运行依赖。",
  );
  const colX = [115, 360, 605, 850, 1082];
  const boxes = [
    ["用户 / 浏览器", "文字 · 语音 · 弹窗", C.tealPale, C.teal],
    ["Web UI", "原生 HTML / CSS / JS", C.card, C.line],
    ["Agent + Planner", "意图识别与多轮记忆", C.card, C.line],
    ["第 10 个工具", "schedule_query", "#FFF4EC", C.orange],
    ["REST / 事件", "ThreadingHTTPServer", C.card, C.line],
  ];
  boxes.forEach(([title, detail, fill, stroke], index) => {
    addCard(slide, colX[index] - 70, 232, 170, 120, fill, stroke);
    addText(slide, title, { left: colX[index] - 50, top: 260, width: 130, height: 32 }, {
      fontSize: "15pt",
      bold: true,
      alignment: "center",
    });
    addText(slide, detail, { left: colX[index] - 54, top: 300, width: 138, height: 36 }, {
      fontSize: "9.5pt",
      color: C.inkSoft,
      alignment: "center",
    });
    if (index < boxes.length - 1) {
      slide.shapes.add({
        geometry: "rightArrow",
        position: { left: colX[index] + 103, top: 280, width: 34, height: 20 },
        fill: C.orange,
        line: { style: "solid", fill: "none", width: 0 },
      });
    }
  });
  addRule(slide, 96, 410, 962, C.line);
  const services = [
    ["Agent", "规划器、工具调用、记忆", "复用"],
    ["Planner", "规则 / 大模型", "复用"],
    ["ToolBox", "9 + 1 工具", "复用"],
    ["Memory", "20 轮 + 长期事实", "复用"],
    ["Scheduler", "once / daily / interval", "新增"],
    ["Voice", "浏览器 ASR / TTS", "新增"],
    ["Device", "接口 + 模拟状态", "新增"],
  ];
  services.forEach(([title, detail, tag], index) => {
    const x = 66 + (index % 4) * 280;
    const y = index < 4 ? 456 : 566;
    addCard(slide, x, y, 248, 82, C.card, C.line);
    addText(slide, title, { left: x + 16, top: y + 12, width: 142, height: 24 }, {
      fontSize: "13pt",
      bold: true,
    });
    addText(slide, detail, { left: x + 16, top: y + 40, width: 176, height: 22 }, {
      fontSize: "9pt",
      color: C.inkSoft,
    });
    addText(slide, tag, { left: x + 192, top: y + 14, width: 42, height: 20 }, {
      fontSize: "8pt",
      bold: true,
      color: tag === "新增" ? C.orangeDark : C.teal,
      alignment: "right",
    });
  });
  slide.speakerNotes.text =
    "架构页。必须清楚说出复用四个、新增三个，以及工具数量为什么仍是 10。";
}

// 09 Stack and deployment
{
  const slide = addBaseSlide(
    presentation,
    9,
    "08 / Delivery",
    "技术栈尽量小，部署脚本让验收者可以自己跑起来",
    "没有 npm 安装、没有服务器框架、没有云端账号依赖；本机有 Python 就能启动。",
  );
  const rows = [
    ["层级", "实际技术", "选择原因"],
    ["前端", "HTML + CSS + 原生 JavaScript", "启动快、界面可直接检查"],
    ["后端", "Python 3.8 + ThreadingHTTPServer", "标准库、零第三方依赖"],
    ["数据", "SQLite + JSON 记忆文件", "单机持久化，备份简单"],
    ["测试", "unittest + PowerShell 验收 + Playwright 截图", "覆盖逻辑、接口和真实 UI"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 3,
    left: 66,
    top: 194,
    width: 620,
    height: 294,
    columnWidths: [100, 248, 272],
    values: rows,
  });
  styleTable(table);
  table.rows[0].height = 42;
  for (let row = 1; row < rows.length; row += 1) table.rows[row].height = 60;
  addText(slide, "部署流程", { left: 728, top: 194, width: 300, height: 30 }, {
    fontSize: "18pt",
    bold: true,
  });
  const deploy = [
    ["01", "安装 Python 3.8+"],
    ["02", "运行 verify_alpha.ps1"],
    ["03", "运行 run_alpha.ps1"],
    ["04", "浏览器打开 127.0.0.1:8765"],
  ];
  deploy.forEach(([number, text], index) => {
    const y = 244 + index * 92;
    addText(slide, number, { left: 730, top: y, width: 40, height: 30 }, {
      fontSize: "12pt",
      bold: true,
      color: C.orangeDark,
    });
    addText(slide, text, { left: 778, top: y - 2, width: 378, height: 46 }, {
      fontSize: "14pt",
      bold: index === 3,
    });
    if (index < deploy.length - 1) addRule(slide, 778, y + 46, 350, C.line);
  });
  addCard(slide, 66, 526, 1118, 96, "#FFF4EC", C.orange);
  addText(slide, "复现入口", { left: 90, top: 544, width: 160, height: 26 }, {
    fontSize: "11pt",
    bold: true,
    color: C.orangeDark,
  });
  addText(slide, "liuhaobin/DeskBirdApp/verify_alpha.ps1   ·   liuhaobin/DeskBirdApp/run_alpha.ps1", {
    left: 90,
    top: 576,
    width: 1030,
    height: 30,
  }, { fontSize: "14pt", bold: true });
  slide.speakerNotes.text =
    "技术与部署。强调标准库与零第三方依赖，现场可以直接跑验收脚本。";
}

// 10 Problems and solutions
{
  const slide = addBaseSlide(
    presentation,
    10,
    "09 / Problems",
    "主要问题都落在“可执行、可测试、可演示”三个边界上",
    "解决方式是把隐含假设变成代码、测试或复现步骤，而不是用解释掩盖。",
  );
  const rows = [
    ["问题", "根因", "解决与证据"],
    ["静态原型无法执行", "前端状态与真实后端脱节", "接入 REST、SQLite、调度器；26 个测试"],
    ["工具数量易膨胀", "提醒增删查改若都做工具会破坏 10 个口径", "提醒作为核心服务；仅新增 schedule_query"],
    ["语音失败会中断", "ASR 依赖浏览器与网络", "识别失败自动回到文字输入"],
    ["周期提醒重复触发", "扫描与时间推进没有测试控制", "注入 now，覆盖 daily / interval 重排"],
    ["Windows 请求乱码", "PowerShell JSON 编码不一致", "验收脚本改用 UTF-8 字节"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 3,
    left: 66,
    top: 194,
    width: 1118,
    height: 412,
    columnWidths: [268, 360, 490],
    values: rows,
  });
  styleTable(table);
  table.rows[0].height = 44;
  for (let row = 1; row < rows.length; row += 1) table.rows[row].height = 72;
  addText(slide, "经验：能让别人独立复现的修复，才算真正完成。", {
    left: 66,
    top: 624,
    width: 1118,
    height: 34,
  }, { fontSize: "16pt", bold: true, color: C.orangeDark, alignment: "center" });
  slide.speakerNotes.text =
    "问题页。每个问题都要能对应代码或日志，不泛泛讲“遇到了困难”。";
}

// 11 Testing
{
  const slide = addBaseSlide(
    presentation,
    11,
    "10 / Quality",
    "测试先覆盖最容易出错的边界，再做演示",
    "测试工具为 Python unittest、PowerShell 一键验收和 Playwright 真实页面检查。",
  );
  addMetric(slide, 70, 164, "26", "自动化测试全部通过", C.teal);
  addMetric(slide, 250, 164, "10", "公共工具全部可用", C.teal);
  addMetric(slide, 430, 164, "0", "第三方运行依赖", C.teal);
  slide.charts.add("bar", {
    position: { left: 690, top: 176, width: 480, height: 400 },
    categories: ["交互接口", "意图解析", "提醒调度", "网页集成"],
    series: [{ name: "测试数", values: [5, 7, 7, 7], fill: C.orange }],
    title: "26 个测试的覆盖分布",
    titleTextStyle: { typeface: FONT, fontSize: 14, bold: true, color: C.ink },
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 44 },
    hasLegend: false,
    xAxis: { visible: false, majorGridlines: null },
    yAxis: {
      textStyle: { typeface: FONT, color: C.inkSoft, fontSize: 11 },
      line: { style: "solid", fill: C.line, width: 1 },
    },
    dataLabels: {
      showValue: true,
      position: "outEnd",
      textStyle: { typeface: FONT, color: C.ink, fontSize: 12, bold: true },
    },
    textStyle: { typeface: FONT, color: C.inkSoft, fontSize: 11 },
  });
  const checks = [
    ["接口与行为", "提醒完成、推迟、到期事件只返回一次"],
    ["解析与边界", "今天 / 明天 / 星期 / 每日 / 间隔"],
    ["调度正确性", "once 变 done，daily 和 interval 自动排下一次"],
    ["真实页面", "Playwright 检查 10 工具、无横向溢出、弹窗可见"],
  ];
  checks.forEach(([title, detail], index) => {
    const y = 300 + index * 78;
    addText(slide, title, { left: 72, top: y, width: 220, height: 26 }, {
      fontSize: "14pt",
      bold: true,
    });
    addText(slide, detail, { left: 72, top: y + 30, width: 540, height: 40 }, {
      fontSize: "10.5pt",
      color: C.inkSoft,
    });
    addRule(slide, 72, y + 68, 540, C.line);
  });
  addText(slide, "测试评述：逻辑和接口覆盖充分；真实语音、不同浏览器和 ESP32 需要现场专项验证。", {
    left: 72,
    top: 622,
    width: 1110,
    height: 30,
  }, { fontSize: "11pt", bold: true, color: C.teal });
  slide.speakerNotes.text =
    "测试页。26 个通过是当前事实，不声称覆盖率 100%，也不声称真实硬件已验证。";
}

// 12 Acceptance matrix
{
  const slide = addBaseSlide(
    presentation,
    12,
    "11 / Acceptance",
    "A1-A10 已有明确状态，未完成项被保留为下一轮工作",
    "现场演示聚焦已完成的 A1、A2、A3、A4、A5、A6、A7、A8；A9/A10 不冒充完成。",
  );
  const rows = [
    ["验收项", "功能", "当前状态", "证据 / 下一步"],
    ["A1", "语音/文字记日程", "完成", "对话与提醒面板"],
    ["A2", "到点提醒", "完成", "气泡 + 浏览器 TTS"],
    ["A3", "10 分钟再提醒", "完成", "推迟动作与测试"],
    ["A4", "周期提醒", "完成", "daily / interval 测试"],
    ["A5", "多轮上下文", "完成", "Memory 20 轮"],
    ["A6", "工具与安全", "完成", "10 工具 + 危险输入拒绝"],
    ["A7", "长期记忆", "完成", "memory.json 持久化"],
    ["A8", "断网核心可用", "完成", "离线规划器 + 本地提醒"],
    ["A9", "硬件联动", "未完成", "Day 11 模拟或 ESP32"],
    ["A10", "上线运行", "部分完成", "本地可运行；云端地址待部署"],
  ];
  const table = slide.tables.add({
    rows: rows.length,
    columns: 4,
    left: 66,
    top: 190,
    width: 1118,
    height: 465,
    columnWidths: [112, 230, 150, 626],
    values: rows,
  });
  styleTable(table);
  table.rows[0].height = 40;
  for (let row = 1; row < rows.length; row += 1) table.rows[row].height = 39;
  for (let row = 1; row < rows.length; row += 1) {
    const status = table.getCell(row, 2);
    status.fill = rows[row][2] === "完成" ? "#E2F1EB" : "#FFF0E7";
    status.text.style = {
      typeface: FONT,
      fontSize: "9.5pt",
      bold: true,
      color: rows[row][2] === "完成" ? C.teal : C.orangeDark,
      alignment: "center",
      verticalAlignment: "middle",
    };
  }
  slide.speakerNotes.text =
    "验收矩阵。完成项来自代码和测试，未完成项必须公开说明，现场不要夸大。";
}

// 13 Member learning
{
  const slide = addBaseSlide(
    presentation,
    13,
    "12 / Reflection",
    "每位成员的过程体会在冲刺结束后由本人确认",
    "本页只放角色与需要回答的问题；不代替成员编造感受，也不把计划分工写成实际经历。",
  );
  const members = [
    ["刘浩彬", "架构 / 后端", "如何把设计约束落成可测代码"],
    ["邓家俊", "PM / 测试", "哪个异常分支改变了验收判断"],
    ["曲浩宾", "前端 / 文档", "原型与真实数据如何统一"],
    ["李忠林", "测试 / 演示", "现场演示暴露了哪些真实问题"],
    ["段旷卓", "前端", "语音失败时如何保持体验连续"],
    ["李彦峰", "后端 / 运维", "部署与数据一致性如何验证"],
    ["刘俊宁", "测试 / 文档", "文档口径如何避免与实现漂移"],
  ];
  members.forEach(([name, role, prompt], index) => {
    const column = index % 2;
    const row = Math.floor(index / 2);
    const x = 66 + column * 558;
    const y = 190 + row * 110;
    addCard(slide, x, y, 536, 92, C.card, C.line);
    addText(slide, name, { left: x + 18, top: y + 14, width: 100, height: 24 }, {
      fontSize: "13pt",
      bold: true,
    });
    addText(slide, role, { left: x + 116, top: y + 16, width: 148, height: 20 }, {
      fontSize: "9pt",
      color: C.teal,
    });
    addText(slide, prompt, { left: x + 18, top: y + 48, width: 490, height: 30 }, {
      fontSize: "10.5pt",
      color: C.inkSoft,
    });
  });
  addCard(slide, 66, 596, 1118, 56, "#FFF4EC", C.orange);
  addText(slide, "提交要求：每人 100-180 字，至少包含一个具体问题、一次协作和一次改进。", {
    left: 88,
    top: 612,
    width: 1070,
    height: 26,
  }, { fontSize: "11pt", bold: true, color: C.orangeDark });
  slide.speakerNotes.text =
    "成员体会页。正式答辩前必须由 7 人填写并替换本页提示语。";
}

// 14 Closing
{
  const slide = presentation.slides.add();
  slide.background.fill = C.ink;
  addText(slide, "报时鸟", { left: 72, top: 100, width: 650, height: 70 }, {
    fontSize: "38pt",
    bold: true,
    color: C.white,
  });
  addText(slide, "Alpha 版本现在可以复现", { left: 72, top: 184, width: 760, height: 72 }, {
    fontSize: "31pt",
    bold: true,
    color: "#FFD4BE",
  });
  addText(slide, "verify_alpha.ps1  →  26 测试通过  →  10 工具可用\nrun_alpha.ps1     →  127.0.0.1:8765  →  作品演示", {
    left: 74,
    top: 294,
    width: 760,
    height: 110,
  }, { fontSize: "17pt", color: "#D9E6E1", lineSpacing: 1.45 });
  addCard(slide, 72, 466, 760, 100, "#263B35", "#45665B");
  addText(slide, "GitHub  github.com/Siruetto/liuhaobin\nAlpha 材料  liuhaobin/AlphaSprint/  ·  Release  v0.1.0-alpha.1", {
    left: 94,
    top: 486,
    width: 710,
    height: 62,
  }, { fontSize: "13pt", color: C.white, lineSpacing: 1.4 });
  addText(slide, "把记性交给机器，把专注留给学习。", { left: 846, top: 236, width: 330, height: 160 }, {
    fontSize: "27pt",
    bold: true,
    color: "#FFB68E",
    lineSpacing: 1.22,
  });
  addText(slide, "谢谢老师，请多指正", { left: 848, top: 600, width: 300, height: 40 }, {
    fontSize: "14pt",
    color: "#A9BBB4",
  });
  slide.speakerNotes.text =
    "收尾。现场运行验收脚本，随后进入 3 分钟 Vlog；总演示控制在 10 分钟内。";
}

const requirements = {
  explicitTotalSlideCount: 14,
  requiredNativeTableOwnerSlides: [4, 5, 9, 10, 12],
  requiredNativeChartOwnerSlides: [6, 11],
  tableArithmeticContracts: [
    {
      slide: 4,
      table: 1,
      label_column: 0,
      total_row: 8,
      value_columns: [3, 4],
      component_rows: [1, 2, 3, 4, 5, 6, 7],
    },
  ],
  materializeLiteralChartWorkbooks: true,
};

const fontPolicy = {
  basis: "design",
  families: [FONT, "Arial"],
};
const expectedSlideSizeEmu = "12192000,6858000";

const selectedPreviews = await presentation.render();
for (let index = 0; index < selectedPreviews.length; index += 1) {
  const preview = selectedPreviews[index];
  const bytes = new Uint8Array(await preview.arrayBuffer());
  await fs.writeFile(
    path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.png`),
    bytes,
  );
}

const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable:
    "C:\\Program Files\\WindowsApps\\OpenAI.CodexPrimaryRuntime.v26-1116-1220-0_26.1116.1220.0_x64__3k8sg7r9htsxt\\dependencies\\python\\python.exe",
  integrityValidatorPath: path.join(
    skillDir,
    "container_tools",
    "inspect_presentation_package_integrity.py",
  ),
  layoutValidatorPath: path.join(
    skillDir,
    "container_tools",
    "inspect_presentation_layout_geometry.py",
  ),
  layoutArgs: [
    "--expected-slide-size-emu",
    expectedSlideSizeEmu,
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    ...[4, 5, 9, 10, 12].flatMap((number) => [
      "--require-native-table-slide",
      String(number),
    ]),
  ],
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "validation.json"),
});

console.log(JSON.stringify({
  finalPath,
  slideCount: presentation.slides.items.length,
  validation: result,
}, null, 2));
