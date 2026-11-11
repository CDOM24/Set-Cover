"""Certificado de cota LP en racionales, sin optimizar ni certificar el optimo entero."""
from fractions import Fraction
import math

def certify_dual(matrix,costs,raw_dual):
    rows=[list(map(int,row)) for row in matrix]
    c=[Fraction(str(v)) for v in costs]
    y=[max(Fraction(0),Fraction(str(v))) for v in raw_dual]
    if len(y)!=len(rows) or len(c)!=len(rows[0]):
        raise ValueError('Dimensiones del dual incompatibles.')
    activities=[sum((y[i]*rows[i][j] for i in range(len(rows))),Fraction(0)) for j in range(len(c))]
    scale=min([Fraction(1)]+[cost/value for cost,value in zip(c,activities) if value>0])
    y=[value*scale for value in y]
    activities=[sum((y[i]*rows[i][j] for i in range(len(rows))),Fraction(0)) for j in range(len(c))]
    assert all(value>=0 for value in y)
    assert all(value<=cost for value,cost in zip(activities,c))
    bound=sum(y,Fraction(0))
    def encoded(q):
        return {'numerador':str(q.numerator),'denominador':str(q.denominator)}
    return {'valida':True,'tipo':'cota_inferior_por_dual_factible_racional','y':list(map(encoded,y)),
            'factor_reescala':encoded(scale),'cota_racional':encoded(bound),'cota_decimal_aproximada':float(bound),
            'cota_entera_si_costos_enteros':math.ceil(bound) if all(q.denominator==1 for q in c) else None,
            'desigualdades_verificadas':len(c),'no_certifica_optimo_entero':True,
            'demostracion':'y>=0 y A^T y<=c implican sum(y)<=c^T x para todo x>=0 con Ax>=1.'}
