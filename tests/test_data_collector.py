import pytest
from unittest.mock import patch, MagicMock
from core.data_collector import CommoditiesCollector

@pytest.fixture
def collector():
    return CommoditiesCollector()

@patch('requests.get')
def test_cepea_collection_success(mock_get, collector):
    """Testa coleta bem-sucedida da CEPEA."""
    # Configura mock
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = """
    <div class="price-box">
        <h3>R$ 158,50</h3>
        <div class="variation"><span>+2,3%</span></div>
    </div>
    """
    
    # Executa
    result = collector.get_cepea_prices()
    
    # Verifica
    assert result["price"] == 158.50
    assert result["variation"] == "+2,3%"
    assert result["source"] == "CEPEA/ESALQ"
    mock_get.assert_called_once()

@patch('yfinance.download')
def test_b3_data_collection(mock_yf, collector):
    """Testa coleta de dados da B3."""
    # Configura mock
    mock_yf.return_value = MagicMock()
    mock_yf.return_value.__getitem__.return_value = MagicMock()
    mock_yf.return_value.__getitem__.return_value.iloc = [15.85]
    
    # Executa
    result = collector.get_b3_data()
    
    # Verifica
    assert result["price"] == 15.85
    assert result["source"] == "B3"

def test_alert_engine_price_drop(collector):
    """Testa geração de alerta de queda de preço."""
    from core.alert_engine import AlertEngine
    from core.db import MockDatabase
    
    # Dados simulados
    current_data = {
        "cepea": {"price": 150.0},
        "usd": {"rate": 5.24},
        "inmet": {"avg_rainfall_mm": 120}
    }
    
    # Banco de dados simulado
    db = MockDatabase(last_price=160.0, historical_avg=145.0)
    engine = AlertEngine(db)
    
    # Executa
    alerts = engine.check_price_alerts(current_data)
    
    # Verifica
    assert len(alerts) == 2  # Queda de preço + Preço acima da média
    assert alerts[0]["type"] == "PRICE_DROP"
    assert "5%" in alerts[0]["message"]