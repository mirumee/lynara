from unittest.mock import AsyncMock, Mock, patch

from lynara.interfaces import APIGatewayProxyEventV2Interface, LifespanInterface
from lynara.runner import Lynara
from lynara.types import LifespanMode


async def test_runner(lambda_events):
    lambda_event = lambda_events["api_gw_v2"]
    mock_app = AsyncMock()
    mock_interface = AsyncMock()
    mock_interface_class = Mock(spec=APIGatewayProxyEventV2Interface)
    mock_interface_class.return_value = mock_interface
    mock_lifespan = AsyncMock()

    lynara = Lynara(mock_app)

    with patch(
        "lynara.runner.LifespanInterface", spec=LifespanInterface
    ) as mock_lifespan_class:
        mock_lifespan_class.return_value = mock_lifespan
        await lynara.run(lambda_event, None, mock_interface_class)

    mock_interface_class.assert_called_once_with(
        app=mock_app, event=lambda_event, context=None, base_path=None
    )
    mock_interface.assert_called_once()
    mock_lifespan_class.assert_called_once_with(
        app=mock_app,
        lifespan_mode=LifespanMode.AUTO,
    )
