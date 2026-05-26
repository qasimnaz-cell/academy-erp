/**
 * AcademyERP — Google Apps Script Backend
 * Deploy as Web App: Execute as "Me", Access "Anyone"
 *
 * Endpoints (POST with JSON body { action, ...params }):
 *   getStudents, addStudent, updatePayment,
 *   getExpenses, addExpense,
 *   getRevenue,  addRevenue,
 *   getSplits,   addSplit, settleSplit,
 *   getMonthlyReport, sendPaymentReminder
 */

const SS_ID = PropertiesService.getScriptProperties().getProperty("SPREADSHEET_ID");
const ss     = () => SpreadsheetApp.openById(SS_ID);

const SHEETS = {
  students:    "Students",
  payments:    "Payments",
  expenses:    "Expenses",
  revenue:     "Revenue",
  splits:      "SplitExpenses",
  settlements: "Settlements",
  logs:        "AuditLogs",
};

// ── Router ─────────────────────────────────────────────────────────────────

function doPost(e) {
  try {
    const body   = JSON.parse(e.postData.contents);
    const action = body.action;
    const result = dispatch(action, body);
    return jsonResponse({ ok: true, data: result });
  } catch (err) {
    return jsonResponse({ ok: false, error: err.message }, 500);
  }
}

function doGet(e) {
  const action = e.parameter.action;
  if (!action) return jsonResponse({ ok: false, error: "action required" }, 400);
  try {
    const result = dispatch(action, e.parameter);
    return jsonResponse({ ok: true, data: result });
  } catch (err) {
    return jsonResponse({ ok: false, error: err.message }, 500);
  }
}

function dispatch(action, params) {
  switch (action) {
    case "getStudents":       return getStudents();
    case "addStudent":        return addStudent(params);
    case "updatePayment":     return updatePayment(params);
    case "getExpenses":       return getSheet(SHEETS.expenses);
    case "addExpense":        return addExpense(params);
    case "getRevenue":        return getSheet(SHEETS.revenue);
    case "addRevenue":        return addRevenue(params);
    case "getSplits":         return getSheet(SHEETS.splits);
    case "addSplit":          return addSplit(params);
    case "settleSplit":       return settleSplit(params);
    case "getMonthlyReport":  return getMonthlyReport(params.month);
    case "sendReminder":      return sendPaymentReminder(params.studentId);
    default: throw new Error(`Unknown action: ${action}`);
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

function getSheet(name) {
  const ws   = ss().getSheetByName(name);
  const data = ws.getDataRange().getValues();
  if (data.length < 2) return [];
  const headers = data[0];
  return data.slice(1).map(row =>
    Object.fromEntries(headers.map((h, i) => [h, row[i]]))
  );
}

function appendRow(name, row) {
  ss().getSheetByName(name).appendRow(row);
}

function jsonResponse(obj, code = 200) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function nowISO() {
  return new Date().toISOString();
}

function generateId(prefix) {
  return `${prefix}-${new Date().getTime()}`;
}

// ── Students ───────────────────────────────────────────────────────────────

function getStudents() {
  return getSheet(SHEETS.students).map(s => ({
    ...s,
    Balance: Number(s.MonthlyFee) - Number(s.PaidAmount),
  }));
}

function addStudent(p) {
  const id = generateId("STU");
  appendRow(SHEETS.students, [
    id, p.name, p.contact, p.email, p.course,
    Number(p.monthly_fee), 0, Number(p.monthly_fee),
    p.enrollment_date || new Date().toISOString().slice(0, 10),
    "Active",
  ]);
  auditLog("system", "addStudent", id);
  return { student_id: id };
}

function updatePayment(p) {
  const ws   = ss().getSheetByName(SHEETS.students);
  const data = ws.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === p.student_id) {
      const paid = Number(data[i][6]) + Number(p.amount);
      const bal  = Number(data[i][5]) - paid;
      ws.getRange(i + 1, 7).setValue(paid);
      ws.getRange(i + 1, 8).setValue(bal);
      appendRow(SHEETS.payments, [
        nowISO(), p.student_id, data[i][1],
        Number(p.amount), paid, bal, p.note || "", "manual",
      ]);
      auditLog(p.recorded_by || "system", "payment", `${p.student_id}:${p.amount}`);
      return { ok: true, new_paid: paid, new_balance: bal };
    }
  }
  throw new Error(`Student not found: ${p.student_id}`);
}

// ── Expenses ───────────────────────────────────────────────────────────────

function addExpense(p) {
  appendRow(SHEETS.expenses, [
    nowISO(), p.date, p.description, p.category,
    Number(p.amount), p.paid_by || "", p.receipt_url || "",
    p.department || "", p.is_recurring || false, p.notes || "",
  ]);
  return { ok: true };
}

// ── Revenue ────────────────────────────────────────────────────────────────

function addRevenue(p) {
  appendRow(SHEETS.revenue, [
    nowISO(), p.date, p.source, p.description,
    Number(p.amount), p.notes || "",
  ]);
  return { ok: true };
}

// ── Split Expenses ─────────────────────────────────────────────────────────

function addSplit(p) {
  const id = generateId("SPL");
  appendRow(SHEETS.splits, [
    id, nowISO(), p.description, Number(p.total_amount),
    p.split_type, p.participants, p.shares, p.paid_by, "unsettled",
  ]);
  return { split_id: id };
}

function settleSplit(p) {
  const ws   = ss().getSheetByName(SHEETS.splits);
  const data = ws.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === p.split_id) {
      ws.getRange(i + 1, 9).setValue("settled");
      appendRow(SHEETS.settlements, [nowISO(), p.split_id, p.settled_by]);
      return { ok: true };
    }
  }
  throw new Error(`Split not found: ${p.split_id}`);
}

// ── Monthly Report ─────────────────────────────────────────────────────────

function getMonthlyReport(month) {
  if (!month) month = Utilities.formatDate(new Date(), "UTC", "yyyy-MM");

  function filterMonth(rows, dateField) {
    return rows.filter(r => String(r[dateField] || "").slice(0, 7) === month);
  }

  const expenses = filterMonth(getSheet(SHEETS.expenses), "Date");
  const revenue  = filterMonth(getSheet(SHEETS.revenue),  "Date");

  const totalRevenue  = revenue.reduce((s, r)  => s + Number(r.Amount), 0);
  const totalExpenses = expenses.reduce((s, e) => s + Number(e.Amount), 0);
  const netProfit     = totalRevenue - totalExpenses;

  // Category breakdowns
  const expByCategory = {};
  expenses.forEach(e => {
    expByCategory[e.Category] = (expByCategory[e.Category] || 0) + Number(e.Amount);
  });

  return {
    month, totalRevenue, totalExpenses, netProfit,
    profitMargin: totalRevenue ? ((netProfit / totalRevenue) * 100).toFixed(2) : 0,
    expensesByCategory: expByCategory,
    transactionCount: expenses.length + revenue.length,
  };
}

// ── Email Reminders ────────────────────────────────────────────────────────

function sendPaymentReminder(studentId) {
  const students = getStudents();
  const student  = students.find(s => s.StudentID === studentId);
  if (!student) throw new Error(`Student not found: ${studentId}`);
  if (!student.Email) throw new Error(`No email for student: ${studentId}`);

  MailApp.sendEmail({
    to:      student.Email,
    subject: `[${APP_TITLE}] Payment Reminder — ${student.Name}`,
    htmlBody: `
      <h2>Payment Reminder</h2>
      <p>Dear <strong>${student.Name}</strong>,</p>
      <p>This is a reminder that your course fee payment is due.</p>
      <table border="1" cellpadding="8" style="border-collapse:collapse;">
        <tr><td><strong>Course</strong></td><td>${student.Course}</td></tr>
        <tr><td><strong>Monthly Fee</strong></td><td>PKR ${Number(student.MonthlyFee).toLocaleString()}</td></tr>
        <tr><td><strong>Outstanding Balance</strong></td><td>PKR ${Number(student.Balance).toLocaleString()}</td></tr>
      </table>
      <p>Please make your payment at the earliest convenience.</p>
      <p>Thank you,<br>AcademyERP Team</p>
    `,
  });
  return { ok: true, sent_to: student.Email };
}

// ── Scheduled Triggers ─────────────────────────────────────────────────────

/**
 * Run monthly: send reminders to all students with outstanding balance.
 * Set trigger: Time-driven → Month timer → 1st of each month
 */
function monthlyReminderJob() {
  const students = getStudents().filter(s => Number(s.Balance) > 0 && s.Email);
  students.forEach(s => {
    try { sendPaymentReminder(s.StudentID); }
    catch(e) { Logger.log(`Reminder failed for ${s.StudentID}: ${e.message}`); }
  });
  Logger.log(`Sent ${students.length} payment reminders`);
}

/**
 * Daily backup: copy current data to a timestamped sheet.
 * Set trigger: Time-driven → Day timer → midnight
 */
function dailyBackup() {
  const stamp  = Utilities.formatDate(new Date(), "UTC", "yyyyMMdd");
  const backup = ss().insertSheet(`Backup_${stamp}`);
  getSheet(SHEETS.students).forEach((row, i) => {
    if (i === 0) backup.appendRow(Object.keys(row));
    backup.appendRow(Object.values(row));
  });
}

// ── Audit Log ──────────────────────────────────────────────────────────────

function auditLog(user, action, detail = "") {
  appendRow(SHEETS.logs, [nowISO(), user, action, detail]);
}

// ── Apps Script Bootstrap ──────────────────────────────────────────────────
// Run once to set up sheet headers.
function bootstrapSheets() {
  const headers = {
    Students:     ["StudentID","Name","Contact","Email","Course","MonthlyFee","PaidAmount","Balance","EnrollmentDate","Status"],
    Payments:     ["Timestamp","StudentID","Name","Amount","TotalPaid","Balance","Note","Source"],
    Expenses:     ["Timestamp","Date","Description","Category","Amount","PaidBy","Receipt","Department","IsRecurring","Notes"],
    Revenue:      ["Timestamp","Date","Source","Description","Amount","Notes"],
    SplitExpenses:["SplitID","Timestamp","Description","TotalAmount","SplitType","Participants","Shares","PaidBy","Status"],
    Settlements:  ["Timestamp","SplitID","SettledBy"],
    AuditLogs:    ["Timestamp","User","Action","Detail"],
  };

  const spreadsheet = ss();
  Object.entries(headers).forEach(([name, cols]) => {
    let ws = spreadsheet.getSheetByName(name);
    if (!ws) ws = spreadsheet.insertSheet(name);
    ws.getRange(1, 1, 1, cols.length).setValues([cols]);
    ws.getRange(1, 1, 1, cols.length).setFontWeight("bold");
  });

  Logger.log("Bootstrap complete ✅");
}
