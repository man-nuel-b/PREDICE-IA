"""Datos ficticios recreados a partir de las categorías del prototipo MERMA360 v2."""
from datetime import date, timedelta
from math import sin


def sample_data(today=None):
    today=today or date.today()
    items=[
        ('DEMO-001','YOG-NAT','Yogur natural 125 g','Refrigerados','Local Temuco','un',175,620,990,4,23,10),
        ('DEMO-002','TOM-ROJ','Tomates frescos','Frutas y verduras','Local Temuco','kg',128,850,1450,3,17,8),
        ('DEMO-003','PAN-MAR','Pan de molde','Panadería','Local Padre Las Casas','un',90,900,1700,7,8,10),
        ('DEMO-004','FRU-ROJ','Frutillas frescas','Frutas y verduras','Local Padre Las Casas','kg',52,1500,2900,2,7,5),
        ('DEMO-005','CER-AV','Avena envasada','Abarrotes','Local Temuco','un',95,1500,2300,95,3,180),
    ]
    lots=[]; sales=[];waste=[]
    for code,sku,name,cat,loc,unit,qty,cost,price,expires,rate,shelf in items:
        lots.append({'code':code,'sku':sku,'name':name,'category':cat,'location':loc,'unit':unit,
            'quantity':qty,'unit_cost':cost,'unit_price':price,'expires_on':(today+timedelta(days=expires)).isoformat(),
            'manual_daily_sales':rate,'shelf_life_days':shelf})
        for days_ago in range(27,-1,-1):
            day=today-timedelta(days=days_ago)
            demand=max(0,round(rate*(1+0.17*sin(days_ago*.65)+(0.12 if day.weekday() in (4,5) else 0))))
            sales.append({'sku':sku,'location':loc,'sold_on':day.isoformat(),'quantity':demand,'unit_price':price})
        waste.append({'sku':sku,'location':loc,'occurred_on':(today-timedelta(days=5)).isoformat(),
            'quantity':1 if cat=='Abarrotes' else 3,'unit_cost':cost})
    return {'lots':lots,'sales':sales,'waste':waste}
