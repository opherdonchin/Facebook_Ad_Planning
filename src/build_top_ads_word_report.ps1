param(
    [Parameter(Mandatory = $true)]
    [string]$JsonPath,

    [Parameter(Mandatory = $true)]
    [string]$BundleRoot,

    [Parameter(Mandatory = $true)]
    [string]$OutputDocx,

    [Parameter(Mandatory = $true)]
    [string]$OutputPdf
)

$ErrorActionPreference = "Stop"

$jsonFile = (Resolve-Path $JsonPath).Path
$bundleDir = (Resolve-Path $BundleRoot).Path
$docxPath = [System.IO.Path]::GetFullPath($OutputDocx)
$pdfPath = [System.IO.Path]::GetFullPath($OutputPdf)

if (Test-Path $docxPath) {
    Remove-Item $docxPath -Force
}
if (Test-Path $pdfPath) {
    Remove-Item $pdfPath -Force
}

$data = Get-Content $jsonFile -Raw -Encoding utf8 | ConvertFrom-Json

$wdPageBreak = 7
$wdFormatDocumentDefault = 16
$wdExportFormatPdf = 17
$wdPreferredWidthPoints = 3
$wdCellAlignTop = 0
$imageColumnWidth = 160
$copyColumnWidth = 340
$maxImageWidth = 150
$maxImageHeight = 220

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null

try {
    $doc = $word.Documents.Add()
    $doc.PageSetup.TopMargin = 36
    $doc.PageSetup.BottomMargin = 36
    $doc.PageSetup.LeftMargin = 40
    $doc.PageSetup.RightMargin = 40

    $script:sel = $word.Selection

    function Add-Line([string]$Text, [int]$Size = 10, [int]$Bold = 0) {
        $script:sel.Font.Name = "Calibri"
        $script:sel.Font.Size = $Size
        $script:sel.Font.Bold = $Bold
        $script:sel.ParagraphFormat.SpaceAfter = 4
        $script:sel.ParagraphFormat.LineSpacingRule = 0
        $script:sel.TypeText($Text)
        $script:sel.TypeParagraph()
    }

    $index = 0
    foreach ($item in $data) {
        if ($index -gt 0) {
            $script:sel.InsertBreak($wdPageBreak)
        }
        $index += 1

        Add-Line "#$($item.rank) $($item.ad_name)" 16 1
        Add-Line (
            "{0} lifetime leads | {1:N2} CPL | {2:N2} ILS spend" -f
            [int]$item.lifetime_leads,
            [double]$item.lifetime_cpl,
            [double]$item.lifetime_spend
        ) 10 0

        $table = $doc.Tables.Add($script:sel.Range, 1, 2)
        $table.Borders.Enable = 0
        $table.AllowAutoFit = $false
        $table.Rows.AllowBreakAcrossPages = 0
        $table.Range.Font.Name = "Calibri"
        $table.Range.Font.Size = 10
        $table.Columns.Item(1).PreferredWidthType = $wdPreferredWidthPoints
        $table.Columns.Item(1).PreferredWidth = $imageColumnWidth
        $table.Columns.Item(2).PreferredWidthType = $wdPreferredWidthPoints
        $table.Columns.Item(2).PreferredWidth = $copyColumnWidth

        $creativePath = Join-Path $bundleDir (($item.creative_file -replace "/", "\"))
        $cell1 = $table.Cell(1, 1).Range
        $shape = $cell1.InlineShapes.AddPicture($creativePath)
        $shape.LockAspectRatio = -1

        $originalWidth = [double]$shape.Width
        $originalHeight = [double]$shape.Height
        $widthScale = $maxImageWidth / $originalWidth
        $heightScale = $maxImageHeight / $originalHeight
        $scale = [Math]::Min(1.0, [Math]::Min($widthScale, $heightScale))

        if ($scale -lt 1.0) {
            $shape.Width = [Math]::Round($originalWidth * $scale, 2)
        }

        $textLabel = [string]$item.text_name
        if ($item.text_variant) {
            $textLabel = "$textLabel ($($item.text_variant))"
        }

        $copyText = @(
            "Headline",
            [string]$item.headline_text,
            "",
            "Primary text",
            [string]$item.primary_text,
            "",
            "Text asset: $textLabel"
        ) -join "`r"

        $cell2 = $table.Cell(1, 2).Range
        $cell2.End = $cell2.End - 1
        $cell2.Text = $copyText
        $table.Cell(1, 1).VerticalAlignment = $wdCellAlignTop
        $table.Cell(1, 2).VerticalAlignment = $wdCellAlignTop

        $script:sel.SetRange($table.Range.End, $table.Range.End)
        $script:sel.TypeParagraph()
    }

    $doc.SaveAs2($docxPath, $wdFormatDocumentDefault)
    $doc.ExportAsFixedFormat($pdfPath, $wdExportFormatPdf)
    $doc.Close(0)
    $doc = $null

    Write-Output "Created $docxPath"
    Write-Output "Created $pdfPath"
}
finally {
    if ($doc -ne $null) {
        try {
            $doc.Close(0)
        }
        catch {
        }
    }
    $word.Quit()
}
