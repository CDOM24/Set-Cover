# Auditoría independiente de SOLO LECTURA de originales y selecciones.
# Desde PowerShell: .\scripts\auditar_powershell.ps1
$ErrorActionPreference='Stop'
$raizAuditoria=(Get-Location).Path
if(-not (Test-Path -LiteralPath (Join-Path $raizAuditoria 'resultados\indice.json'))){throw 'Ejecutar desde la raíz de Set-Cover.'}
$trazas=Get-Content -LiteralPath (Join-Path $raizAuditoria 'resultados\procedencia.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach($traza in $trazas){
 $ruta=(Join-Path $raizAuditoria $traza.archivo)
 if((Get-FileHash -LiteralPath $ruta -Algorithm SHA256).Hash.ToLower() -ne $traza.sha256){throw ('Hash distinto: '+$traza.archivo)}
}
$lineas=[System.IO.File]::ReadAllLines((Join-Path $raizAuditoria 'datos\set_cover_500x500.csv'))
if($lineas.Length -ne 501){throw 'CSV debe tener 500 filas y encabezado'}
$etiquetas=$lineas[0].Trim([char]0xFEFF).Split(',')
if($etiquetas.Length -ne 500){throw 'CSV debe tener 500 columnas'}
for($j=0;$j -lt 500;$j++){if($etiquetas[$j] -ne [string]$j){throw 'Orden CSV no válido'}}
$matriz=[System.Collections.Generic.List[object]]::new()
$unos=0
for($i=1;$i -le 500;$i++){
 $fila=$lineas[$i].Split(',')
 if($fila.Length -ne 500){throw 'Fila irregular'}
 foreach($celda in $fila){if($celda -notin @('0','1')){throw 'CSV no binario'};if($celda -eq '1'){$unos++}}
 $matriz.Add($fila)
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archivoZip=[System.IO.Compression.ZipFile]::OpenRead((Join-Path $raizAuditoria 'datos\Costo_S.xlsx'))
try{
 $entrada=$archivoZip.GetEntry('xl/worksheets/sheet1.xml')
 $lector=[System.IO.StreamReader]::new($entrada.Open())
 try{[xml]$hoja=$lector.ReadToEnd()}finally{$lector.Dispose()}
 $ns=[System.Xml.XmlNamespaceManager]::new($hoja.NameTable);$ns.AddNamespace('s','http://schemas.openxmlformats.org/spreadsheetml/2006/main')
 $ids=@($hoja.SelectNodes('//s:sheetData/s:row[@r="1"]/s:c',$ns) | Where-Object {$_.r -ne 'A1'})
 $costos=@($hoja.SelectNodes('//s:sheetData/s:row[@r="2"]/s:c',$ns) | Where-Object {$_.r -ne 'A2'})
 if($ids.Count -ne 500 -or $costos.Count -ne 500){throw 'Se necesitan 500 IDs y 500 costos'}
 $valoresCosto=[System.Collections.Generic.List[decimal]]::new()
 for($j=0;$j -lt 500;$j++){
  if([int]$ids[$j].v -ne $j+1){throw 'Orden Excel no válido'}
  $valor=[decimal]::Parse([string]$costos[$j].v,[System.Globalization.CultureInfo]::InvariantCulture)
  if($valor -lt 0){throw 'Costo negativo'}
  $valoresCosto.Add($valor)
 }
}finally{$archivoZip.Dispose()}
$indice=Get-Content -LiteralPath (Join-Path $raizAuditoria 'resultados\indice.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$comprobadas=[System.Collections.Generic.List[object]]::new()
foreach($entradaResultado in $indice){
 $documento=Get-Content -LiteralPath (Join-Path $raizAuditoria $entradaResultado.archivo) -Raw -Encoding UTF8 | ConvertFrom-Json
 if($documento.PSObject.Properties['resultado']){$r=$documento.resultado}else{$r=$documento}
 $seleccion=@($r.seleccion)
 if($seleccion.Count -ne 500){throw 'Selección de longitud incorrecta'}
 $elegidas=[System.Collections.Generic.List[int]]::new();[decimal]$total=0
 for($j=0;$j -lt 500;$j++){
  if($seleccion[$j] -notin @(0,1)){throw 'Selección no binaria'}
  if($seleccion[$j] -eq 1){$elegidas.Add($j);$total+=$valoresCosto[$j]}
 }
 $cubiertos=0
 foreach($fila in $matriz){$conteo=0;foreach($j in $elegidas){$conteo += [int]$fila[$j]};if($conteo -ge 1){$cubiertos++}}
 switch($entradaResultado.esquema){
  'highs_adicional'{$costoEsperado=$r.mejor_costo_verificado;$cota=$r.cota_inferior_corrida;$certificado=$r.optimalidad_certificada;$tiempo=$r.tiempo_solver_segundos}
  'scip_adicional'{$costoEsperado=$r.mejor_costo_verificado;$cota=$r.cota_inferior_propia;$certificado=$r.optimalidad_certificada;$tiempo=$r.tiempo_optimizacion_monotonico_segundos}
  default{$costoEsperado=$r.costo_total;$cota=$r.mejor_cota;if($entradaResultado.metodo -eq 'AG'){$certificado=$r.optimalidad_demostrada}else{$certificado=$r.optimalidad_certificada_solver};$tiempo=$r.tiempo_ag_segundos}
 }
 if($total -ne [decimal]$costoEsperado -or $cubiertos -ne 500 -or $r.numero_antenas -ne $elegidas.Count -or $r.clientes_cubiertos -ne 500){throw ('Auditoría rechazada: '+$entradaResultado.archivo)}
 if($certificado){throw 'Esta entrega no debe declarar optimalidad certificada'}
 $comprobadas.Add([pscustomobject]@{etiqueta=$entradaResultado.etiqueta;metodo=$entradaResultado.metodo;costo=$total;antenas=$elegidas.Count;clientes=$cubiertos;cota=$cota;tiempo=$tiempo})
}
$mejorAg=($comprobadas | Where-Object metodo -eq 'AG' | Measure-Object costo -Minimum).Minimum
$mejorGlobal=($comprobadas | Measure-Object costo -Minimum).Minimum
$mejorCota=($comprobadas | Where-Object {$null -ne $_.cota} | Measure-Object cota -Maximum).Maximum
if($comprobadas.Count -ne 26 -or $mejorAg -ne 49051 -or $mejorGlobal -ne 48878 -or [math]::Abs($mejorCota-34532.73615154492) -gt 0.00001){throw 'Valores de referencia distintos'}
[pscustomobject]@{
 tipo='auditoria_independiente_PowerShell_Decimal_sin_optimizacion'
 archivos_verificados=$trazas.Count
 corridas=$comprobadas.Count
 entradas_uno=$unos
 mejor_ag=$mejorAg
 mejor_global=$mejorGlobal
 cota_inferior=$mejorCota
 separacion_comun_porcentaje=100*($mejorGlobal-$mejorCota)/$mejorGlobal
 optimo_certificado=$false
 resultados=@($comprobadas.ToArray())
} | ConvertTo-Json -Depth 8