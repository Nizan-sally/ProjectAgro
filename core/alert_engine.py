from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import telegram
import logging
from config.settings import ALERT_RECIPIENTS

logger = logging.getLogger(__name__)

class AlertEngine:
    """Sistema de alertas com múltiplos canais e lógica contextual para agronegócio."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def check_price_alerts(self, current_data):
        """Verifica condições para alertas baseados em indicadores do agronegócio."""
        last_price = self.db.get_last_price("soja")
        if not last_price:
            return []
        
        alerts = []
        current = current_data["cepea"]["price"] if current_data["cepea"] else None
        usd = current_data["usd"]["rate"] if current_data["usd"] else None
        
        if not current or not usd:
            return alerts
        
        # Regra 1: Queda > 5% em 24h
        if (last_price - current) / last_price > 0.05:
            alerts.append({
                "type": "PRICE_DROP",
                "message": f"⚠️ Queda de {round(((last_price - current)/last_price)*100, 1)}% no preço da soja",
                "severity": "HIGH",
                "context": f"Preço atual: R$ {current} | Dólar: R$ {usd}\n"
                           "Impacto potencial nas exportações brasileiras"
            })
        
        # Regra 2: Preço acima da média histórica
        historical_avg = self.db.get_historical_avg("soja", days=30)
        if historical_avg and current > historical_avg * 1.1:
            alerts.append({
                "type": "PRICE_HIGH",
                "message": f"📈 Preço da soja 10% acima da média histórica ({historical_avg:.2f})",
                "severity": "MEDIUM",
                "context": "Oportunidade para venda estratégica no mercado interno e externo"
            })
        
        # Regra 3: Correlação clima-preço
        if current_data["inmet"] and current_data["inmet"]["avg_rainfall_mm"] < 20:
            alerts.append({
                "type": "DROUGHT_RISK",
                "message": f"🌧️ Baixa precipitação em {current_data['inmet']['state']} (<20mm)",
                "severity": "HIGH",
                "context": "Risco de redução na produção futura - "
                           "prepare-se para volatilidade de preços"
            })
        
        return alerts
    
    def send_alert(self, alert):
        """Envia alerta por múltiplos canais profissionais."""
        timestamp = datetime.now().strftime('%d/%m %H:%M')
        
        # 1. Telegram
        if ALERT_RECIPIENTS["telegram"] and 'TELEGRAM_BOT_TOKEN' in os.environ:
            try:
                bot = telegram.Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
                for chat_id in ALERT_RECIPIENTS["telegram"]:
                    bot.send_message(
                        chat_id=chat_id,
                        text=f"🚨 ALERTA AGRÍCOLA ({alert['severity']})\n\n"
                             f"{alert['message']}\n\n"
                             f"Contexto: {alert['context']}\n"
                             f"Horário: {timestamp}"
                    )
            except Exception as e:
                logger.error(f"Telegram alert failed: {str(e)}", exc_info=True)
        
        # 2. E-mail
        if ALERT_RECIPIENTS["email"]:
            try:
                msg = MIMEText(
                    f"<h2>🚨 ALERTA AGRÍCOLA ({alert['severity']})</h2>"
                    f"<p><strong>{alert['message']}</strong></p>"
                    f"<p><em>{alert['context']}</em></p>"
                    f"<p>Horário: {timestamp}</p>"
                    "<p><small>Este é um alerta automático do Sistema AgroInsight</small></p>",
                    "html"
                )
                msg["Subject"] = f"[ALERTA] {alert['type']} - Commodities Agrícolas"
                msg["From"] = "alertas@agroinsight.com"
                msg["To"] = ", ".join(ALERT_RECIPIENTS["email"])
                
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
                    server.sendmail(msg["From"], ALERT_RECIPIENTS["email"], msg.as_string())
            except Exception as e:
                logger.error(f"Email alert failed: {str(e)}", exc_info=True)
        
        # 3. Log no sistema
        self.db.log_alert(alert)
    
    def run_daily_analysis(self):
        """Executa análise diária completa (para agendamento com cron)."""
        collector = CommoditiesCollector()
        data = collector.collect_all()
        
        # Salva dados no banco
        if all(data.values()):
            self.db.save_commodity_data(data)
        
        # Verifica alertas
        alerts = self.check_price_alerts(data)
        for alert in alerts:
            self.send_alert(alert)
        
        # Gera relatório diário
        if alerts:
            report = ReportGenerator(self.db).generate_daily_report()
            self.send_report(report)