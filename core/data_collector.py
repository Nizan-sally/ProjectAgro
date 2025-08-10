import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import yfinance as yf
import logging
import random
import time

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CommoditiesCollector")

class CommoditiesCollector:
    """Coleta dados de fontes oficiais brasileiras para análise agrícola."""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        }
        # Dados simulados para desenvolvimento
        self.simulated_data = {
            "soja": {
                "price": round(150 + random.uniform(-5, 10), 2),
                "variation": f"{'+' if random.random() > 0.5 else '-'}{round(random.uniform(0.5, 3.0), 1)}%"
            },
            "milho": {
                "price": round(100 + random.uniform(-3, 7), 2),
                "variation": f"{'+' if random.random() > 0.5 else '-'}{round(random.uniform(0.5, 2.5), 1)}%"
            }
        }
    
    def get_cepea_prices(self, commodity="soja"):
        """Coleta preços da CEPEA (Centro de Pesquisa em Economia Aplicada)."""
        logger.info(f"Iniciando coleta CEPEA para {commodity}")
        try:
            url = f"https://www.cepea.esalq.usp.br/br/cotacoes/{commodity}/"
            logger.debug(f"Requesting URL: {url}")
            
            # Adiciona delay para não ser bloqueado
            time.sleep(1.5)
            
            response = requests.get(url, headers=self.headers, timeout=20)
            logger.info(f"CEPEA status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"CEPEA returned status {response.status_code}")
                return self._get_simulated_cepea(commodity)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ATUALIZADO: Seletores para Jun/2024
            price_element = soup.select_one('div.box-cotacao h3')
            variation_element = soup.select_one('div.box-cotacao span.variacao')
            
            if not price_element or not variation_element:
                logger.error("Estrutura do site CEPEA alterada - seletores não encontrados")
                return self._get_simulated_cepea(commodity)
                
            # Limpeza mais robusta
            price_text = price_element.text.strip()
            price = float(price_text.replace("R$", "").replace(" ", "").replace(",", "."))
            
            variation = variation_element.text.strip()
            
            logger.info(f"CEPEA - {commodity}: R$ {price} ({variation})")
            return {
                "commodity": commodity,
                "price": price,
                "variation": variation,
                "source": "CEPEA/ESALQ",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"CEPEA collection failed: {str(e)}", exc_info=True)
            return self._get_simulated_cepea(commodity)
    
    def _get_simulated_cepea(self, commodity):
        """Retorna dados simulados quando a coleta real falha."""
        logger.warning(f"Usando dados simulados para CEPEA/{commodity}")
        data = self.simulated_data.get(commodity, self.simulated_data["soja"])
        return {
            "commodity": commodity,
            "price": data["price"],
            "variation": data["variation"],
            "source": "CEPEA_SIMULADO",
            "timestamp": datetime.now().isoformat()
        }

    def get_b3_data(self):
        """Coleta dados da B3 (soja futura) via Yahoo Finance."""
        logger.info("Iniciando coleta B3")
        try:
            ticker = "ZS=F"  # Soja futura
            logger.debug(f"Baixando dados para {ticker}")
            
            # Período estendido para aumentar chance de sucesso
            data = yf.download(ticker, period="5d", progress=False)
            
            if data.empty:
                logger.warning("Nenhum dado retornado pela Yahoo Finance")
                return self._get_simulated_b3()
                
            last_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            variation = ((last_price - prev_price) / prev_price) * 100
            
            logger.info(f"B3 - Soja Futuro: ${last_price:.2f} ({variation:.2f}%)")
            return {
                "commodity": "soja_futuro",
                "price": round(last_price, 2),
                "variation": f"{variation:+.2f}%",
                "source": "B3/YAHOO",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"B3 collection failed: {str(e)}", exc_info=True)
            return self._get_simulated_b3()
    
    def _get_simulated_b3(self):
        """Retorna dados simulados para B3."""
        logger.warning("Usando dados simulados para B3")
        price = 15.0 + random.uniform(-0.5, 1.0)
        variation = random.uniform(-2.0, 2.0)
        return {
            "commodity": "soja_futuro",
            "price": round(price, 2),
            "variation": f"{variation:+.2f}%",
            "source": "B3_SIMULADO",
            "timestamp": datetime.now().isoformat()
        }

    def get_usd_rate(self):
        """Coleta cotação do dólar (crucial para exportações)."""
        logger.info("Iniciando coleta USD")
        try:
            usd = yf.Ticker("BRL=X")
            data = usd.history(period="1d")
            
            if data.empty:
                logger.warning("Nenhum dado retornado para USD")
                return self._get_simulated_usd()
                
            rate = data['Close'].iloc[-1]
            prev_rate = data['Close'].iloc[-2] if len(data) > 1 else rate
            variation = ((rate - prev_rate) / prev_rate) * 100
            
            logger.info(f"USD - Dólar: R$ {rate:.4f} ({variation:.2f}%)")
            return {
                "currency": "USD",
                "rate": round(rate, 4),
                "variation": f"{variation:+.2f}%",
                "source": "BACEN/YAHOO",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"USD collection failed: {str(e)}", exc_info=True)
            return self._get_simulated_usd()
    
    def _get_simulated_usd(self):
        """Retorna dados simulados para USD."""
        logger.warning("Usando dados simulados para USD")
        rate = 5.0 + random.uniform(-0.2, 0.3)
        variation = random.uniform(-0.5, 0.5)
        return {
            "currency": "USD",
            "rate": round(rate, 4),
            "variation": f"{variation:+.2f}%",
            "source": "USD_SIMULADO",
            "timestamp": datetime.now().isoformat()
        }

    def get_inmet_rainfall(self, state="MT"):
        """Coleta dados pluviométricos do INMET."""
        logger.info(f"Iniciando coleta INMET para {state}")
        try:
            # Data de ontem (INMET atualiza com atraso)
            date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"https://apitempo.inmet.gov.br/estacao/diaria/{date_str}/all"
            logger.debug(f"Requesting INMET URL: {url}")
            
            response = requests.get(url, timeout=15)
            logger.info(f"INMET status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"INMET returned status {response.status_code}")
                return self._get_simulated_inmet(state)
            
            # Filtrando por estado
            rainfall = []
            for d in response.json():
                if d.get('UF') == state and d.get('CHUVA') not in [None, '']:
                    try:
                        rainfall.append(float(d['CHUVA']))
                    except (TypeError, ValueError):
                        continue
            
            avg_rain = sum(rainfall) / len(rainfall) if rainfall else 0
            
            logger.info(f"INMET - {state}: {avg_rain:.1f}mm")
            return {
                "state": state,
                "avg_rainfall_mm": round(avg_rain, 1),
                "source": "INMET",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"INMET collection failed: {str(e)}", exc_info=True)
            return self._get_simulated_inmet(state)
    
    def _get_simulated_inmet(self, state):
        """Retorna dados simulados para INMET."""
        logger.warning(f"Usando dados simulados para INMET/{state}")
        # Simulação realista por região
        if state in ["MT", "MS", "GO"]:
            avg_rain = random.uniform(0, 50)  # Seca comum no Centro-Oeste
        elif state in ["PR", "SC", "RS"]:
            avg_rain = random.uniform(50, 150)  # Mais chuva no Sul
        else:
            avg_rain = random.uniform(20, 100)
        
        return {
            "state": state,
            "avg_rainfall_mm": round(avg_rain, 1),
            "source": "INMET_SIMULADO",
            "timestamp": datetime.now().isoformat()
        }

    def get_conab_production(self, commodity="soja"):
        """Coleta estimativas de produção da CONAB."""
        logger.info(f"Iniciando coleta CONAB para {commodity}")
        try:
            # URL atualizada (Jun/2024)
            url = "https://api.conab.gov.br/v3/safra/2023-2024"
            logger.debug(f"Requesting CONAB URL: {url}")
            
            # CONAB requer User-Agent específico
            headers = {
                **self.headers,
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            logger.info(f"CONAB status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"CONAB returned status {response.status_code}")
                return self._get_simulated_conab(commodity)
            
            # Estrutura atualizada da API
            data = response.json()
            
            # Procura pela commodity nos resultados
            for crop in data.get('resultados', []):
                if crop.get('cultura', '').lower() == commodity:
                    production = float(crop.get('producao', 0))
                    
                    logger.info(f"CONAB - {commodity}: {production} mi t")
                    return {
                        "commodity": commodity,
                        "production_million_tons": production,
                        "state": "BR",
                        "source": "CONAB",
                        "timestamp": datetime.now().isoformat()
                    }
            
            logger.warning(f"Commodity {commodity} não encontrada na resposta da CONAB")
            return self._get_simulated_conab(commodity)
            
        except Exception as e:
            logger.error(f"CONAB collection failed: {str(e)}", exc_info=True)
            return self._get_simulated_conab(commodity)
    
    def _get_simulated_conab(self, commodity):
        """Retorna dados simulados para CONAB."""
        logger.warning(f"Usando dados simulados para CONAB/{commodity}")
        # Produção simulada baseada em médias reais
        if commodity == "soja":
            production = 150 + random.uniform(-10, 15)
        elif commodity == "milho":
            production = 120 + random.uniform(-8, 10)
        else:
            production = 50 + random.uniform(-5, 7)
        
        return {
            "commodity": commodity,
            "production_million_tons": round(production, 1),
            "state": "BR",
            "source": "CONAB_SIMULADO",
            "timestamp": datetime.now().isoformat()
        }

    def collect_all(self):
        """Coleta dados integrados de todas as fontes oficiais."""
        logger.info("Iniciando coleta completa de dados")
        start_time = datetime.now()
        
        result = {
            "cepea": self.get_cepea_prices(),
            "b3": self.get_b3_data(),
            "usd": self.get_usd_rate(),
            "inmet": self.get_inmet_rainfall(),
            "conab": self.get_conab_production()
        }
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Coleta completa realizada em {duration:.2f} segundos")
        
        # Gera arquivo de log detalhado
        with open("collector_summary.log", "w") as f:
            f.write(f"Resumo da coleta - {datetime.now().isoformat()}\n")
            f.write(f"Duração: {duration:.2f} segundos\n\n")
            for source, data in result.items():
                status = "SUCESSO" if data and not data['source'].endswith('_SIMULADO') else "SIMULADO"
                f.write(f"[{source.upper()}] - {status}\n")
                if data:
                    for k, v in data.items():
                        f.write(f"  {k}: {v}\n")
                f.write("\n")
        
        return result

if __name__ == "__main__":
    print("="*50)
    print("INICIANDO COLETA DE DADOS - AGROINSIGHT")
    print("="*50)
    
    collector = CommoditiesCollector()
    data = collector.collect_all()
    
    print("\n" + "="*50)
    print("RESULTADO DA COLETA")
    print("="*50)
    
    for source, result in data.items():
        status = "REAL" if result and not result['source'].endswith('_SIMULADO') else "SIMULADO"
        print(f"\nFonte: {source.upper()} [{status}]")
        if result:
            for k, v in result.items():
                print(f"  {k}: {v}")
        else:
            print("  ERRO: Nenhum dado coletado")
    
    print("\n" + "="*50)
    print(f"Coleta concluída em {datetime.now().strftime('%H:%M:%S')}")
    print("Logs detalhados em: collector.log e collector_summary.log")
    print("="*50)