import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Minimal translation resources (Expandable)
const resources = {
    en: {
        translation: {
            "dashboard": "Dashboard",
            "match_intelligence": "Match Intelligence",
            "key_metrics": "Key Metrics Analysis",
            "atp_rank": "ATP Rank",
            "elo_rating": "ELO Rating",
            "recent_form": "Recent Form",
            "surface_win": "Surface Win%",
            "h2h_wins": "H2H Wins",
            "set_aggression": "Set Aggression",
            "physical_condition": "Physical Condition",
            "fit_to_play": "Fit to Play (Est.)",
            "last_match": "Last Match",
            "analysis_pending": "Analysis pending",
            "no_injury_report": "No significant injury reports found in recent data.",
            "select_player": "Select Player",
            "search_placeholder": "Type name (e.g. 'Alcaraz')...",
            "checklist": "Validation Checklist",
            "metrics_help": {
                "form": "Win % in last 10 matches",
                "surface": "Win % on this specific surface (Hard/Clay/Grass)",
                "elo": "Relative skill level rating",
                "aggression": "Tendency to win sets decisively"
            }
        }
    },
    es: {
        translation: {
            "dashboard": "Panel Principal",
            "match_intelligence": "Inteligencia de Partido",
            "key_metrics": "Análisis de Métricas Clave",
            "atp_rank": "Ranking ATP",
            "elo_rating": "Rating ELO",
            "recent_form": "Forma Reciente",
            "surface_win": "% Victoria Superficie",
            "h2h_wins": "Victorias H2H",
            "set_aggression": "Agresividad por Set",
            "physical_condition": "Condición Física",
            "fit_to_play": "Apto para Jugar (Est.)",
            "last_match": "Último Partido",
            "analysis_pending": "Análisis pendiente",
            "no_injury_report": "No se encontraron reportes de lesiones recientes.",
            "select_player": "Seleccionar Jugador",
            "search_placeholder": "Escribe nombre (ej. 'Alcaraz')...",
            "checklist": "Checklist de Validación",
            "metrics_help": {
                "form": "% Victorias en últimos 10 partidos",
                "surface": "% Victorias en esta superficie",
                "elo": "Nivel de habilidad relativo",
                "aggression": "Tendencia a ganar sets decisivamente"
            }
        }
    },
    pt: { // Portuguese
        translation: {
            "dashboard": "Painel",
            "match_intelligence": "Inteligência de Jogo",
            "key_metrics": "Métricas Chave",
            "atp_rank": "Ranking ATP",
            "elo_rating": "Classificação ELO",
            "recent_form": "Forma Recente",
            "surface_win": "% Vitória Superfície",
            "h2h_wins": "Vitórias H2H",
            "set_aggression": "Agressividade do Set",
            "physical_condition": "Condição Física",
            "fit_to_play": "Apto para Jogar",
            "last_match": "Último Jogo",
            "analysis_pending": "Análise pendente"
        }
    },
    de: { // German
        translation: {
            "dashboard": "Instrumententafel",
            "match_intelligence": "Spielanalyse",
            "key_metrics": "Wichtige Kennzahlen",
            "atp_rank": "ATP-Rangliste",
            "elo_rating": "ELO-Bewertung",
            "recent_form": "Aktuelle Form",
            "surface_win": "Belag Sieg%",
            "h2h_wins": "H2H Siege",
            "set_aggression": "Satz-Aggression",
            "physical_condition": "Physische Verfassung",
            "fit_to_play": "Spielbereit",
            "last_match": "Letztes Spiel",
            "analysis_pending": "Analyse ausstehend"
        }
    },
    it: { translation: { "key_metrics": "Metriche Chiave", "recent_form": "Forma Recente" } },
    fr: { translation: { "key_metrics": "Mesures Clés", "recent_form": "Forme Récente" } },
    zh: { translation: { "key_metrics": "关键指标分析", "recent_form": "近期状态" } },
    ja: { translation: { "key_metrics": "主要指標分析", "recent_form": "最近の調子" } },
    ar: { translation: { "key_metrics": "تحليل المؤشرات الرئيسية", "recent_form": "النموذج الأخير" } },
    ko: { translation: { "key_metrics": "주요 지표 분석", "recent_form": "최근 양식" } },
    ru: { translation: { "key_metrics": "Анализ ключевых показателей", "recent_form": "Текущая форма" } }
};

i18n
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources,
        fallbackLng: 'en',
        interpolation: {
            escapeValue: false
        }
    });

export default i18n;
