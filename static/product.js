const $ = (id) => document.getElementById(id);

function lines(value) {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function optionalNumber(id) {
  const value = $(id).value.trim();
  return value === "" ? null : Number(value);
}

function productPayload() {
  return {
    name: $("name").value.trim(),
    brand: $("brand").value.trim(),
    category: $("category").value.trim(),
    audience: $("audience").value.trim() || "general consumers",
    description: $("description").value.trim(),
    features: lines($("features").value),
    benefits: lines($("benefits").value),
    regular_price: optionalNumber("regular-price"),
    sale_price: optionalNumber("sale-price"),
    currency: $("currency").value.trim() || "THB",
    cta: $("cta").value.trim() || "สั่งซื้อเลย",
    visual_notes: $("visual-notes").value.trim(),
  };
}

function setStatus(message, kind = "") {
  const node = $("status");
  node.textContent = message;
  node.dataset.kind = kind;
}

function renderPlan(data) {
  const plan = data.plan;
  $("empty-state").hidden = true;
  $("plan").hidden = false;
  $("score").textContent = `${plan.score}/100`;
  $("verdict").textContent = plan.verdict.toUpperCase();
  $("verdict").dataset.level = plan.verdict;
  $("aspect").textContent = plan.aspect_ratio;
  $("duration").textContent = `${plan.duration_seconds}s`;
  $("pacing").textContent = plan.pacing;
  $("style").textContent = plan.creative_style;
  $("prompt").textContent = plan.prompt;
  $("negative").textContent = plan.negative_prompt;

  const emphasis = $("emphasis");
  emphasis.replaceChildren(...plan.emphasis.map((item) => {
    const span = document.createElement("span");
    span.className = "chip";
    span.textContent = item;
    return span;
  }));

  const reasons = $("reasons");
  reasons.replaceChildren(...plan.reasons.map((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    return li;
  }));
}

async function analyze(event) {
  event.preventDefault();
  setStatus("กำลังวิเคราะห์สินค้า…");
  try {
    const response = await fetch("/api/v2/products/plan", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(productPayload()),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }
    renderPlan(data);
    setStatus("วิเคราะห์สำเร็จ พร้อมนำ prompt ไป render", "success");
  } catch (error) {
    setStatus(`วิเคราะห์ไม่สำเร็จ: ${error.message}`, "error");
  }
}

function loadExample() {
  $("name").value = "Wireless Mechanical Keyboard";
  $("brand").value = "ExampleBrand";
  $("category").value = "electronics accessory";
  $("audience").value = "gamers and productivity users";
  $("description").value = "Compact mechanical keyboard with wireless connectivity and hot-swappable switches.";
  $("features").value = "2.4GHz wireless\nBluetooth\nHot-swappable switches\nRGB backlight";
  $("benefits").value = "ใช้ได้ทั้งโต๊ะทำงานและเกมมิ่ง\nเปลี่ยนสวิตช์ได้โดยไม่ต้องบัดกรี";
  $("regular-price").value = "2490";
  $("sale-price").value = "2190";
  $("currency").value = "THB";
  $("cta").value = "สั่งซื้อเลย";
  $("visual-notes").value = "Preserve key layout, legends, chassis proportions and supplied product color.";
  setStatus("โหลดตัวอย่างแล้ว กด Analyze product เพื่อสร้างแผน");
}

async function copyText(text, successMessage) {
  try {
    await navigator.clipboard.writeText(text);
    setStatus(successMessage, "success");
  } catch {
    setStatus("คัดลอกไม่สำเร็จ กรุณาเลือกข้อความด้วยตนเอง", "error");
  }
}

$("product-form").addEventListener("submit", analyze);
$("load-example").addEventListener("click", loadExample);
$("copy-json").addEventListener("click", () => copyText(JSON.stringify(productPayload(), null, 2), "คัดลอก Product JSON แล้ว"));
$("copy-prompt").addEventListener("click", () => copyText($("prompt").textContent, "คัดลอก prompt แล้ว"));
$("reset-form").addEventListener("click", () => {
  $("product-form").reset();
  $("currency").value = "THB";
  $("cta").value = "สั่งซื้อเลย";
  $("plan").hidden = true;
  $("empty-state").hidden = false;
  setStatus("");
});
