from flask import Flask, request, jsonify, render_template_string
from groq import Groq
import os, json, re
from datetime import datetime

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Livro Caixa</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Segoe UI, sans-serif; background: #f0f4f8; color: #1a202c; }
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
h1 { text-align: center; color: #2d3748; margin-bottom: 6px; font-size: 1.8rem; }
.sub { text-align: center; color: #718096; margin-bottom: 24px; font-size: 0.9rem; }
.card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.card h2 { font-size: 1rem; color: #4a5568; margin-bottom: 12px; }
.row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
label { font-size: 0.85rem; color: #4a5568; }
select, input { border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 0.9rem; outline: none; }
select:focus, input:focus { border-color: #4299e1; }
textarea { width: 100%; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; font-size: 0.9rem; resize: vertical; min-height: 120px; outline: none; font-family: inherit; }
.btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600; }
.bp { background: #4299e1; color: white; }
.bg { background: #48bb78; color: white; }
.bz { background: #e2e8f0; color: #4a5568; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.spinner { display: none; }
.loading .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; animation: spin 0.7s linear infinite; margin-right: 6px; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }
.result { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 0.82rem; white-space: pre-wrap; max-height: 400px; overflow-y: auto; line-height: 1.6; }
.totals { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; }
.tbox { flex: 1; min-width: 140px; padding: 12px 16px; border-radius: 8px; text-align: center; }
.tbox .lbl { font-size: 0.75rem; color: #718096; margin-bottom: 4px; }
.tbox .val { font-size: 1.2rem; font-weight: 700; }
.te { background: #f0fff4; } .te .val { color: #38a169; }
.ts { background: #fff5f5; } .ts .val { color: #e53e3e; }
.tl { background: #ebf8ff; } .tl .val { color: #2b6cb0; }
.entries { max-height: 300px; overflow-y: auto; margin-top: 10px; }
.entry { display: flex; gap: 8px; align-items: center; padding: 8px; border-bottom: 1px solid #f7fafc; font-size: 0.85rem; }
.entry .dt { color: #718096; min-width: 75px; }
.entry .dc { flex: 1; }
.entry .vl { font-weight: 600; min-width: 100px; text-align: right; }
.entrada { color: #38a169; }
.saida { color: #e53e3e; }
.del { background: none; border: none; color: #cbd5e0; cursor: pointer; font-size: 16px; }
.del:hover { color: #e53e3e; }
.empty { color: #a0aec0; text-align: center; padding: 20px; font-size: 0.85rem; }
.alert { padding: 10px 14px; border-radius: 8px; margin-bottom: 12px; font-size: 0.85rem; }
.ai { background: #ebf8ff; color: #2b6cb0; border: 1px solid #bee3f8; }
.ae { background: #fff5f5; color: #c53030; border: 1px solid #fed7d7; }
</style>
</head>
<body>
<div class="container">
<h1>Livro Caixa</h1>
<p class="sub">Cole textos ou imagens com movimentacoes - a IA extrai os lancamentos automaticamente</p>

<div class="card">
<h2>Configuracao</h2>
<div class="row">
<div><label>Empresa<br><input type="text" id="empresa" placeholder="Nome da empresa" style="width:200px"></label></div>
<div><label>Mes<br>
<select id="mes">
<option>Janeiro</option><option>Fevereiro</option><option>Marco</option>
<option>Abril</option><option>Maio</option><option>Junho</option>
<option>Julho</option><option>Agosto</option><option>Setembro</option>
<option>Outubro</option><option>Novembro</option><option>Dezembro</option>
</select></label></div>
<div><label>Ano<br><input type="text" id="ano" value="2026" style="width:80px"></label></div>
</div>
</div>

<div class="card">
<h2>Colar Informacoes</h2>
<div id="alerta"></div>
<textarea id="txt" placeholder="Cole aqui extratos, mensagens, anotacoes com valores e datas..."></textarea>
<input type="file" id="imgInput" accept="image/*" multiple style="display:none" onchange="addImgs(event)">
<div id="prevs" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px"></div>
<div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap">
<button class="btn bp" id="btnE" onclick="extrair()"><span class="spinner"></span>Extrair com IA</button>
<button class="btn bz" onclick="document.getElementById('imgInput').click()">Adicionar Imagem</button>
<button class="btn bz" onclick="limpar()">Limpar</button>
</div>
</div>

<div class="card">
<h2>Adicionar Manual</h2>
<div class="row" style="flex-wrap:wrap;gap:8px">
<div><label>Data<br><input type="date" id="mD"></label></div>
<div><label>Descricao<br><input type="text" id="mX" placeholder="Ex: Aluguel" style="width:200px"></label></div>
<div><label>Tipo<br><select id="mT"><option value="entrada">Entrada</option><option value="saida">Saida</option></select></label></div>
<div><label>Valor R$<br><input type="number" id="mV" placeholder="0.00" step="0.01" min="0" style="width:120px"></label></div>
<div><label>&nbsp;<br><button class="btn bg" onclick="addM()">Adicionar</button></label></div>
</div>
</div>

<div class="card">
<h2>Lancamentos</h2>
<div class="totals">
<div class="tbox te"><div class="lbl">ENTRADAS</div><div class="val" id="tE">R$ 0,00</div></div>
<div class="tbox ts"><div class="lbl">SAIDAS</div><div class="val" id="tS">R$ 0,00</div></div>
<div class="tbox tl"><div class="lbl">SALDO</div><div class="val" id="tL">R$ 0,00</div></div>
</div>
<div class="entries" id="lista"><div class="empty">Nenhum lancamento ainda.</div></div>
</div>

<div class="card">
<h2>Livro Caixa para Contadora</h2>
<div style="display:flex;gap:10px;margin-bottom:14px">
<button class="btn bp" id="btnG" onclick="gerar()"><span class="spinner"></span>Gerar Livro Caixa</button>
<button class="btn bz" onclick="copiar()">Copiar</button>
</div>
<div class="result" id="resultado">O livro caixa aparecera aqui...</div>
</div>
</div>

<script>
let lans = [];
let imgs = [];
document.getElementById('mes').selectedIndex = new Date().getMonth();

function fmt(v) { return 'R$ ' + Number(v).toFixed(2).replace('.', ','); }

function addImgs(e) {
  for (const f of e.target.files) {
    const r = new FileReader();
    r.onload = ev => {
      const b64 = ev.target.result.split(',')[1];
      const idx = imgs.length;
      imgs.push({base64: b64, mediaType: f.type});
      const d = document.createElement('div');
      d.style = 'position:relative';
      d.innerHTML = '<img src="' + ev.target.result + '" style="width:70px;height:70px;object-fit:cover;border-radius:6px;border:2px solid #e2e8f0">' +
        '<button onclick="rmImg(' + idx + ')" style="position:absolute;top:-6px;right:-6px;background:#e53e3e;color:white;border:none;border-radius:50%;width:18px;height:18px;cursor:pointer;font-size:10px">x</button>';
      document.getElementById('prevs').appendChild(d);
    };
    r.readAsDataURL(f);
  }
}

function rmImg(i) { imgs[i] = null; }

function limpar() {
  document.getElementById('txt').value = '';
  imgs = [];
  document.getElementById('prevs').innerHTML = '';
  document.getElementById('imgInput').value = '';
}

function render() {
  const el = document.getElementById('lista');
  if (!lans.length) { el.innerHTML = '<div class="empty">Nenhum lancamento ainda.</div>'; totais(); return; }
  const s = [...lans].sort((a,b)=>(a.data||'').localeCompare(b.data||''));
  el.innerHTML = s.map((l,i)=>
    '<div class="entry">' +
    '<span class="dt">' + fbr(l.data) + '</span>' +
    '<span class="dc">' + l.descricao + '</span>' +
    '<span class="vl ' + l.tipo + '">' + (l.tipo==='entrada'?'+':'-') + ' ' + fmt(l.valor) + '</span>' +
    '<button class="del" onclick="del(' + i + ')">x</button>' +
    '</div>'
  ).join('');
  totais();
}

function fbr(d) {
  if (!d) return '';
  const p = d.split('-');
  return p[2]+'/'+p[1]+'/'+p[0];
}

function totais() {
  const e = lans.filter(l=>l.tipo==='entrada').reduce((s,l)=>s+Number(l.valor),0);
  const s = lans.filter(l=>l.tipo==='saida').reduce((a,l)=>a+Number(l.valor),0);
  document.getElementById('tE').textContent = fmt(e);
  document.getElementById('tS').textContent = fmt(s);
  const sl = e - s;
  const el = document.getElementById('tL');
  el.textContent = fmt(Math.abs(sl));
  el.style.color = sl >= 0 ? '#2b6cb0' : '#e53e3e';
}

function del(i) { lans.splice(i,1); render(); }

function addM() {
  const d = document.getElementById('mD').value;
  const x = document.getElementById('mX').value.trim();
  const t = document.getElementById('mT').value;
  const v = parseFloat(document.getElementById('mV').value);
  if (!d||!x||!v) { alerta('Preencha data, descricao e valor.','ae'); return; }
  lans.push({data:d, descricao:x, tipo:t, valor:v});
  render();
  document.getElementById('mX').value='';
  document.getElementById('mV').value='';
}

async function extrair() {
  const txt = document.getElementById('txt').value.trim();
  const imgsFilt = imgs.filter(Boolean);
  if (!txt && !imgsFilt.length) { alerta('Cole um texto ou adicione uma imagem.','ae'); return; }
  const btn = document.getElementById('btnE');
  btn.classList.add('loading'); btn.disabled = true;
  try {
    const r = await fetch('/extrair', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({texto:txt, imagens:imgsFilt})});
    const d = await r.json();
    if (d.error) { alerta(d.error,'ae'); return; }
    const n = d.lancamentos || [];
    lans.push(...n);
    render();
    if (n.length) alerta('OK - ' + n.length + ' lancamento(s) extraido(s)!','ai');
    else alerta('Nao encontrei lancamentos. Tente descrever melhor.','ae');
    limpar();
  } catch(e) { alerta('Erro ao processar.','ae'); }
  finally { btn.classList.remove('loading'); btn.disabled=false; }
}

async function gerar() {
  if (!lans.length) { alerta('Adicione lancamentos primeiro.','ae'); return; }
  const btn = document.getElementById('btnG');
  btn.classList.add('loading'); btn.disabled=true;
  try {
    const r = await fetch('/gerar', {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({lancamentos:lans, mes:document.getElementById('mes').value,
        ano:document.getElementById('ano').value, empresa:document.getElementById('empresa').value||'Empresa'})});
    const d = await r.json();
    document.getElementById('resultado').textContent = d.resultado || d.error;
  } catch(e) { document.getElementById('resultado').textContent='Erro ao gerar.'; }
  finally { btn.classList.remove('loading'); btn.disabled=false; }
}

function copiar() {
  navigator.clipboard.writeText(document.getElementById('resultado').textContent)
    .then(()=>alerta('Copiado!','ai'));
}

function alerta(msg, cls) {
  const el = document.getElementById('alerta');
  el.innerHTML = '<div class="alert ' + cls + '">' + msg + '</div>';
  setTimeout(()=>el.innerHTML='', 4000);
}

render();
</script>
</body>
</html>"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/extrair', methods=['POST'])
def extrair():
    data = request.json
    texto = data.get('texto', '')
    imagens = data.get('imagens', [])

    prompt = """Analise o conteudo e extraia TODOS os lancamentos financeiros.
Responda SOMENTE com JSON valido neste formato exato:
{"lancamentos": [{"data": "YYYY-MM-DD", "descricao": "descricao", "tipo": "entrada", "valor": 123.45}]}
Regras:
- tipo entrada = recebimentos vendas depositos creditos
- tipo saida = pagamentos despesas debitos compras
- valor numero positivo sem R$
- ano padrao 2026 se nao informado"""

    content = []
    if texto:
        content.append({"type": "text", "text": f"{prompt}\n\nTexto:\n{texto}"})
    else:
        content.append({"type": "text", "text": prompt})

    for img in imagens:
        if img:
            content.append({"type": "image_url", "image_url": {"url": f"data:{img['mediaType']};base64,{img['base64']}"}})

    if not content:
        return jsonify({"error": "Nada para processar"})

    try:
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": content}],
            temperature=0.1,
            max_tokens=2000
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        result = json.loads(raw)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Erro: {str(e)}", "lancamentos": []})


@app.route('/gerar', methods=['POST'])
def gerar():
    data = request.json
    lancamentos = data.get('lancamentos', [])
    mes = data.get('mes', 'Mes')
    ano = data.get('ano', '2026')
    empresa = data.get('empresa', 'Empresa')

    if not lancamentos:
        return jsonify({"error": "Sem lancamentos"})

    sorted_l = sorted(lancamentos, key=lambda x: x.get('data', ''))
    linhas = []
    for l in sorted_l:
        d = l.get('data', '')
        if d:
            p = d.split('-')
            d = f"{p[2]}/{p[1]}/{p[0]}" if len(p) == 3 else d
        tipo = 'ENTRADA' if l.get('tipo') == 'entrada' else 'SAIDA  '
        valor = f"R$ {float(l.get('valor', 0)):>10.2f}".replace('.', ',')
        desc = l.get('descricao', '')[:45].ljust(45)
        linhas.append(f"  {d}  {tipo}  {desc}  {valor}")

    ent = sum(float(l.get('valor', 0)) for l in lancamentos if l.get('tipo') == 'entrada')
    sai = sum(float(l.get('valor', 0)) for l in lancamentos if l.get('tipo') == 'saida')
    sal = ent - sai

    def brl(v):
        return f"R$ {abs(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    sep = "=" * 74
    resultado = f"""{sep}
                       LIVRO CAIXA MENSAL
{sep}
  Empresa : {empresa}
  Periodo : {mes} / {ano}
  Emissao : {datetime.now().strftime('%d/%m/%Y %H:%M')}
{sep}
  DATA       TIPO      DESCRICAO                                       VALOR
{'-' * 74}
{chr(10).join(linhas)}
{sep}
  TOTAL ENTRADAS . . . . . . . . . . . . . . . . . . . .  {brl(ent):>15}
  TOTAL SAIDAS . . . . . . . . . . . . . . . . . . . . .  {brl(sai):>15}
{'-' * 74}
  SALDO {'POSITIVO' if sal >= 0 else 'NEGATIVO'} . . . . . . . . . . . . . . . . . . . .  {brl(sal):>15}
{sep}
  Total de lancamentos: {len(lancamentos)}
{sep}"""

    return jsonify({"resultado": resultado})


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')