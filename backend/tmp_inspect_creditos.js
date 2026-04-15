const XLSX = require("xlsx");
const wb = XLSX.readFile("../Reporte de Pendientes de Credito.xlsx", { cellDates: true });
const ws = wb.Sheets[wb.SheetNames[0]];
const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: null, raw: false, blankrows: false });
console.log("sheet", wb.SheetNames[0]);
for (let i = 0; i < Math.min(rows.length, 30); i += 1) {
  console.log(String(i + 1), JSON.stringify(rows[i]));
}
