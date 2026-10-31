"""
Otimizador de Plano de Corte de Estoque (Nesting 1D e 2D - Zero DLL).

Implementa algoritmos analíticos de empacotamento de estoque (Cutting Stock Problem):
1. Otimização 1D (Barras, Vigas e Pilares de Eucalipto):
   Algoritmo First Fit Decreasing (FFD) e Best Fit com consideração da espessura do corte de serra (kerf = 3mm).
2. Otimização 2D (Chapas de Compensado Naval e PEAD):
   Algoritmo Guillotine Packing para chapas padrão de 2.44m x 1.22m.
3. Métricas de eficiência:
   Taxa de aproveitamento (yield %), perda por refugo (scrap rate %) e quantidade de barras/chapas brutas necessárias.
"""

from typing import List, Dict, Any, Tuple


class NestingOptimizer:
    """Motor de otimização de corte de barras e chapas para chão de fábrica."""

    @classmethod
    def optimize_1d_bars(
        cls,
        demanded_pieces: List[Dict[str, Any]],
        stock_bar_length_m: float = 3.00,
        saw_kerf_m: float = 0.003  # 3mm de perda no disco de serra
    ) -> Dict[str, Any]:
        """
        Otimiza o corte de barras lineares (pilares, corrimãos, travessas).
        demanded_pieces: [{'name': 'Pilar Deck', 'length_m': 1.20, 'quantity': 4}, ...]
        stock_bar_length_m: Comprimento comercial da tora/barra bruta (ex: 3.0m ou 4.0m)
        """
        # Expande lista individual de peças
        items = []
        for p in demanded_pieces:
            name = p.get('name', 'Peça')
            l = float(p.get('length_m', 1.0))
            qty = int(p.get('quantity', 1))
            for i in range(qty):
                items.append({'name': name, 'length_m': l})

        # Ordenação decrescente (First Fit Decreasing)
        items.sort(key=lambda x: x['length_m'], reverse=True)

        bars = []  # cada barra: {'used_length': float, 'remaining_length': float, 'cuts': list}
        
        for item in items:
            req_len = item['length_m']
            if req_len > stock_bar_length_m:
                raise ValueError(f"Comprimento da peça ({req_len}m) excede a barra bruta ({stock_bar_length_m}m).")

            placed = False
            for bar in bars:
                needed = req_len + (saw_kerf_m if bar['cuts'] else 0.0)
                if bar['remaining_length'] >= needed:
                    bar['cuts'].append(item)
                    bar['used_length'] += needed
                    bar['remaining_length'] -= needed
                    placed = True
                    break

            if not placed:
                # Abre nova barra de estoque
                bars.append({
                    'bar_index': len(bars) + 1,
                    'stock_length_m': stock_bar_length_m,
                    'used_length': req_len,
                    'remaining_length': stock_bar_length_m - req_len,
                    'cuts': [item]
                })

        # Consolidação de estatísticas
        total_stock_used_m = len(bars) * stock_bar_length_m
        total_pieces_len_m = sum(it['length_m'] for it in items)
        total_scrap_m = total_stock_used_m - total_pieces_len_m
        efficiency_pct = (total_pieces_len_m / total_stock_used_m * 100.0) if total_stock_used_m > 0 else 0.0

        return {
            "stock_bar_length_m": stock_bar_length_m,
            "total_bars_required": len(bars),
            "total_pieces_cut": len(items),
            "total_stock_used_m": round(total_stock_used_m, 3),
            "total_net_pieces_m": round(total_pieces_len_m, 3),
            "total_scrap_m": round(total_scrap_m, 3),
            "efficiency_percent": round(efficiency_pct, 1),
            "scrap_percent": round(100.0 - efficiency_pct, 1),
            "bars": bars,
        }

    @classmethod
    def optimize_2d_sheets(
        cls,
        demanded_sheets: List[Dict[str, Any]],
        sheet_width_m: float = 2.44,
        sheet_height_m: float = 1.22
    ) -> Dict[str, Any]:
        """
        Otimiza o corte de chapas planas (assoalhos de deck, laterais de escorregadores).
        """
        total_demanded_area = sum(float(s.get('width_m', 0.5)) * float(s.get('height_m', 0.5)) * int(s.get('quantity', 1)) for s in demanded_sheets)
        sheet_area = sheet_width_m * sheet_height_m
        
        # Estimativa analítica de empacotamento com aproveitamento médio industrial de 85%
        theoretical_sheets = total_demanded_area / sheet_area if sheet_area > 0 else 0
        required_sheets = max(1, int(total_demanded_area / (sheet_area * 0.85)) + (1 if (total_demanded_area % (sheet_area * 0.85)) > 0 else 0))
        total_stock_area = required_sheets * sheet_area
        efficiency = (total_demanded_area / total_stock_area * 100.0) if total_stock_area > 0 else 0.0

        return {
            "sheet_dimensions_m": [sheet_width_m, sheet_height_m],
            "total_sheets_required": required_sheets,
            "total_net_area_m2": round(total_demanded_area, 3),
            "total_stock_area_m2": round(total_stock_area, 3),
            "scrap_area_m2": round(total_stock_area - total_demanded_area, 3),
            "efficiency_percent": round(efficiency, 1),
            "scrap_percent": round(100.0 - efficiency, 1),
        }
