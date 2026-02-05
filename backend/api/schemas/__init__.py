"""
Marshmallow schemas for request validation
Provides input validation for API endpoints
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class OrderSchema(Schema):
    """Schema for order placement and modification"""
    
    symbol = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=20),
        error_messages={'required': 'Symbol is required'}
    )
    
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=100000),
        error_messages={'required': 'Quantity is required'}
    )
    
    order_type = fields.Str(
        required=True,
        validate=validate.OneOf(['MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LOSS_MARKET']),
        error_messages={'required': 'Order type is required'}
    )
    
    price = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0.01)
    )
    
    trigger_price = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0.01)
    )
    
    product_type = fields.Str(
        required=True,
        validate=validate.OneOf(['INTRADAY', 'DELIVERY', 'CO', 'OCO']),
        error_messages={'required': 'Product type is required'}
    )
    
    exchange = fields.Str(
        required=True,
        validate=validate.OneOf(['NSE', 'BSE', 'NFO', 'MCX']),
        error_messages={'required': 'Exchange is required'}
    )
    
    @validates_schema
    def validate_price_for_limit_order(self, data, **kwargs):
        """Ensure price is provided for LIMIT orders"""
        if data.get('order_type') == 'LIMIT' and not data.get('price'):
            raise ValidationError('Price is required for LIMIT orders', 'price')
    
    @validates_schema
    def validate_trigger_price(self, data, **kwargs):
        """Ensure trigger_price is provided for stop-loss orders"""
        if data.get('order_type') in ['STOP_LOSS', 'STOP_LOSS_MARKET']:
            if not data.get('trigger_price'):
                raise ValidationError(
                    'Trigger price required for stop-loss orders',
                    'trigger_price'
                )


class AlertSchema(Schema):
    """Schema for alert creation"""
    
    symbol = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=20)
    )
    
    condition = fields.Str(
        required=True,
        validate=validate.OneOf(['ABOVE', 'BELOW', 'CROSSES_ABOVE', 'CROSSES_BELOW'])
    )
    
    target_price = fields.Float(
        required=True,
        validate=validate.Range(min=0.01)
    )
    
    notification_method = fields.Str(
        validate=validate.OneOf(['EMAIL', 'SMS', 'TELEGRAM', 'PUSH'])
    )
    
    enabled = fields.Bool(missing=True)


class StrategySchema(Schema):
    """Base schema for trading strategies"""
    
    symbol = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=20)
    )
    
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=100000)
    )


class CalendarSpreadSchema(StrategySchema):
    """Schema for calendar spread strategy"""
    
    strike_price = fields.Float(
        required=True,
        validate=validate.Range(min=0.01)
    )
    
    near_expiry = fields.Date(required=True)
    far_expiry = fields.Date(required=True)
    
    @validates_schema
    def validate_expiry_dates(self, data, **kwargs):
        """Ensure far expiry is after near expiry"""
        if data.get('far_expiry') <= data.get('near_expiry'):
            raise ValidationError(
                'Far expiry must be after near expiry',
                'far_expiry'
            )


class BacktestSchema(Schema):
    """Schema for backtest configuration"""
    
    strategy_name = fields.Str(
        required=True,
        validate=validate.OneOf(['RSI', 'MACD', 'SMA_CROSSOVER', 'BOLLINGER_BANDS'])
    )
    
    symbol = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=20)
    )
    
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    
    initial_capital = fields.Float(
        missing=100000.0,
        validate=validate.Range(min=1000.0)
    )
    
    parameters = fields.Dict(missing={})
    
    @validates_schema
    def validate_date_range(self, data, **kwargs):
        """Ensure end date is after start date"""
        if data.get('end_date') <= data.get('start_date'):
            raise ValidationError(
                'End date must be after start date',
                'end_date'
            )


__all__ = [
    'OrderSchema',
    'AlertSchema',
    'StrategySchema',
    'CalendarSpreadSchema',
    'BacktestSchema',
]
