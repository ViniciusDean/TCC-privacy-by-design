import * as vscode from 'vscode';
import { Finding } from './contract';

function riskToSeverity(risk: string): vscode.DiagnosticSeverity {
    switch (risk) {
        case 'ALTO': return vscode.DiagnosticSeverity.Error;
        case 'MEDIO': return vscode.DiagnosticSeverity.Warning;
        case 'BAIXO': return vscode.DiagnosticSeverity.Information;
        default: return vscode.DiagnosticSeverity.Information;
    }
}

export function buildDiagnostics(
    uri: vscode.Uri,
    findings: Finding[],
    isIgnored: (finding: Finding) => boolean
): vscode.Diagnostic[] {
    const diagnostics: vscode.Diagnostic[] = [];
    for (const finding of findings) {
        if (finding.linha <= 0 || isIgnored(finding)) {
            continue;
        }
        const range = new vscode.Range(
            new vscode.Position(finding.linha - 1, 0),
            new vscode.Position(finding.linha - 1, 1000)
        );
        const diagnostic = new vscode.Diagnostic(
            range,
            `${finding.categoria} [confiança ${finding.confianca || 'ALTA'}]: ${finding.evidencia_segura}${finding.artigo_lgpd ? `\n${finding.artigo_lgpd}` : ''}`,
            riskToSeverity(finding.risco)
        );
        diagnostic.code = finding.categoria;
        diagnostic.source = 'Privacy Scanner';
        if (finding.recomendacao) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(uri, range),
                    `Correção: ${finding.recomendacao}`
                )
            ];
        }
        diagnostics.push(diagnostic);
    }
    return diagnostics;
}
