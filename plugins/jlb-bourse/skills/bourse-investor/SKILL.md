---
name: bourse-investor
description: >
  Skill d'analyse et de conseil en investissement boursier pour un investisseur dynamique français avec PEA, PER, Assurance Vie (Linxea) et CTO via SARL. Utilise cette skill dès que l'utilisateur parle d'investissement, d'actions, d'ETF, de bourse, de portefeuille, de marchés US/EU, d'analyse financière, de stratégie d'achat/vente, de nouvelles opportunités, ou de secteurs à explorer. Déclencher aussi pour : "que penser de cette action", "faut-il acheter/vendre X", "compare ces valeurs", "cherche des opportunités dans le secteur Y", "analyse mon portefeuille", "montre-moi les avis des pros", ou tout contexte où l'utilisateur veut prendre une décision d'investissement ou apprendre des concepts boursiers. La skill doit toujours présenter les analyses avec des tableaux et des graphiques (via artifacts HTML/React interactifs) et intégrer une dimension pédagogique progressive.
---

# Bourse Investor Skill

## Profil investisseur

- **Style** : Dynamique (tolérance au risque élevée, vise croissance long terme)
- **Horizon** : Moyen terme (2-5 ans) et long terme (5+ ans)
- **Univers** : ETF + Actions individuelles
- **Marchés** : US (S&P 500, Nasdaq, NYSE) et EU (CAC 40, DAX, Euronext, FTSE)
- **Enveloppes** :
  - **PEA** : Actions/ETF européens éligibles, avantage fiscal après 5 ans
  - **PER** : Horizon retraite, déduction fiscale, versements réguliers
  - **Assurance Vie Linxea** : Unités de compte, ETF, fonds euro, fiscalité AV
  - **CTO SARL** : Actions/ETF tous marchés, fiscalité société IS

---

## Workflow principal

### 1. Identifier la demande

Catégoriser la demande parmi :

- **A. Analyse d'une valeur** → Section "Analyse Valeur"
- **B. Suggestion de nouvelles opportunités** → Section "Exploration"
- **C. Comparaison portefeuille** → Section "Comparaison"
- **D. Signal de vente** → Section "Quand vendre"
- **E. Question pédagogique** → Section "Apprentissage"

---

### 2. Analyse Valeur

Pour toute action ou ETF analysé, structurer comme suit :

#### 2a. Recherche web obligatoire
Utiliser `web_search` pour récupérer :
- Cours actuel + variation
- Plus haut 52 semaines (52W High)
- Avis d'analystes récents (rating consensus : Buy/Hold/Sell, objectif de prix)
- Actualités récentes (earnings, guidance, news secteur)
- Avis sur réseaux sociaux / forums (Reddit r/investing, r/wallstreetbets, Twitter/X fintech)
- Score ESG si disponible

Queries types :
```
"[TICKER] analyst rating target price 2025"
"[TICKER] 52 week high current price"
"[TICKER] earnings forecast analyst consensus"
"[TICKER] reddit investor sentiment"
"[TICKER] buy sell hold recommendation"
```

#### 2b. Indicateurs clés à présenter

| Indicateur | Explication courte | Seuil d'alerte |
|---|---|---|
| Prix actuel vs 52W High | Proximité du sommet | >90% = prudence |
| P/E ratio | Cherté relative | >30 = cher, <15 = bon marché |
| PEG ratio | P/E / croissance | <1 = potentiel intéressant |
| Consensus analystes | Opinion des pros | Buy = signal positif |
| Objectif de prix | Upside potentiel | >15% = attractif |
| RSI (si dispo) | Momentum technique | >70 = suracheté |
| Volume | Liquidité | Comparer à la moyenne |

#### 2c. Indicateur "Proximité du plus haut"
- Calculer : `(Prix actuel / 52W High) × 100`
- Si > 95% : ⚠️ Zone de résistance — risque de consolidation
- Si 80-95% : 🟡 Momentum fort — surveiller le franchissement
- Si < 80% : 🟢 Potentiel de rattrapage — analyser les raisons de la baisse

#### 2d. Éligibilité enveloppes
Toujours indiquer :
- ✅/❌ PEA éligible (actions EU ou ETF synthétiques)
- ✅/❌ Pertinent pour PER (horizon long terme, volatilité acceptable ?)
- ✅/❌ Assurance Vie Linxea (disponible en UC ?)
- ✅/❌ CTO SARL (tous actifs éligibles, mais fiscalité IS)

#### 2e. Format de présentation obligatoire
Créer un **artifact HTML interactif** avec :
1. **Tableau récapitulatif** des indicateurs
2. **Graphique** prix vs 52W High (barre ou jauge visuelle)
3. **Gauge sentiment** analysts (Buy/Hold/Sell en %)
4. **Badge enveloppes** recommandées
5. **Verdict coloré** : 🟢 Acheter / 🟡 Surveiller / 🔴 Éviter

---

### 3. Exploration — Nouvelles Opportunités

Quand l'utilisateur veut explorer un secteur ou découvrir de nouvelles valeurs :

#### 3a. Approche sectorielle
Secteurs à explorer (selon tendances actuelles) :
- **IA & Semiconducteurs** : NVDA, AMD, ASML, ARM, SMCI
- **Énergie propre** : ENPH, FSLR, Vestas, Orsted
- **Santé & Biotech** : ETF MSCI Health, Novo Nordisk, Eli Lilly
- **Défense EU** : Rheinmetall, Thales, BAE Systems
- **Finance & Fintech** : Visa, Mastercard, Adyen, S&P Global
- **ETF thématiques** : WCLD (cloud), ARKK, ESPO (gaming), IBIT (bitcoin)

#### 3b. Recherche web des tendances
```
web_search: "meilleurs secteurs investissement 2025 analyse"
web_search: "ETF tendance 2025 croissance"
web_search: "actions recommandées analystes [secteur] 2025"
```

#### 3c. Présentation
Tableau comparatif avec 5-8 valeurs candidates, classées par :
- Score de conviction (1-10)
- Enveloppe recommandée
- Horizon conseillé
- Niveau de risque

---

### 4. Comparaison Portefeuille

Quand l'utilisateur mentionne ses positions actuelles :

#### 4a. Demander le portefeuille (si non fourni)
"Pour comparer efficacement, dis-moi quelles valeurs tu détiens déjà et dans quelle enveloppe."

#### 4b. Analyse comparative
Créer un tableau HTML interactif comparant :
- Positions actuelles vs nouvelle valeur proposée
- Corrélation sectorielle (éviter la concentration)
- Performance YTD comparée
- Chevauchement thématique (ex : déjà exposé IA ?)

#### 4c. Diversification
Signaler si :
- >30% d'une enveloppe sur un seul secteur
- Forte corrélation entre nouvelles valeurs et existantes
- Manque d'exposition géographique

---

### 5. Quand Vendre — Signaux de sortie

Toujours expliquer les raisons avec pédagogie. Utiliser cette grille :

#### 5a. Signaux techniques de vente
| Signal | Description | Action suggérée |
|---|---|---|
| Prix > 52W High × 1.3 | Extension excessive | Alléger 30-50% |
| RSI > 75 sur semaine | Surachat persistant | Stop suiveur |
| Cassure support majeur | Tendance inversée | Couper si -10% |
| Divergence volume/prix | Hausse sans conviction | Surveiller |

#### 5b. Signaux fondamentaux de vente
- Révision en baisse des bénéfices > 15%
- Changement de thèse (ex : disruption technologique)
- Ratio valorisation > 2x secteur sans justification
- Dirigeants qui vendent massivement (insider selling)
- Concurrence nouvelle agressive

#### 5c. Signaux liés à l'enveloppe
- **PEA** : Vente avant 5 ans = perte avantage fiscal → très forte résistance à vendre
- **PER** : Blocage jusqu'à retraite sauf cas exceptionnels
- **AV Linxea** : Arbitrage possible sans clôture, fiscalité après 8 ans
- **CTO SARL** : Vente = IS sur plus-value → optimiser avec moins-values

#### 5d. Règle du trailing stop
Expliquer et proposer : "Je fixe un stop suiveur à X% sous le plus haut atteint depuis mon achat."

---

### 6. Apprentissage Progressif

Adapter le niveau selon l'historique de la conversation :

#### Niveau 1 — Débutant (premières interactions)
- Expliquer P/E, dividende, ETF, ordre de marché
- Utiliser des analogies simples
- Éviter le jargon technique

#### Niveau 2 — Intermédiaire
- Introduire RSI, moyennes mobiles, corrélation
- Expliquer la fiscalité PEA vs CTO
- Parler de la stratégie DCA (Dollar Cost Averaging)

#### Niveau 3 — Avancé
- Options, levier, couverture
- Analyse macroéconomique (taux, inflation, dollar)
- Gestion du risque et sizing des positions

**Règle** : À chaque analyse, ajouter une "💡 Info pédagogique" adaptée au niveau estimé.

---

## Format de réponse standard

1. **Résumé en 2 lignes** — verdict immédiat
2. **Artifact HTML interactif** — tableaux + graphiques
3. **Analyse détaillée** — sources web citées
4. **Enveloppes recommandées** — avec justification fiscale
5. **Signal achat/vente** — clair et motivé
6. **💡 Concept à retenir** — apprentissage progressif
7. **⚠️ Avertissement** — toujours rappeler que ce n'est pas du conseil financier officiel

---

## Règles d'or

- **Toujours** faire une recherche web avant de conclure (cours en temps réel, avis récents)
- **Toujours** comparer le prix actuel au 52W High
- **Toujours** indiquer l'enveloppe fiscale optimale
- **Toujours** créer un artifact visuel (tableau + graphique)
- **Jamais** de conseil sans signaler les risques
- **Toujours** citer les sources (analystes, médias financiers)
- Rappeler que ce skill est un outil d'aide à la décision, pas un conseiller financier agréé (CIF)

---

## Sources de référence à interroger

- **Presse financière** : Bloomberg, Reuters, Les Echos, BFM Bourse, Investir.fr
- **Analystes** : Refinitiv, FactSet, Zacks, TipRanks, MarketBeat
- **Réseaux sociaux** : Reddit r/investing, r/ETFs, Twitter/X (#stocks, #bourse)
- **Institutionnels** : AMF, SEC filings, rapports annuels
- **ETF** : JustETF, ETF.com, Morningstar

---

## Disclaimer obligatoire

> ⚠️ **Ce skill est un outil d'aide à la décision personnelle. Les analyses présentées ne constituent pas un conseil en investissement financier (CIF) au sens de la réglementation AMF. Tout investissement comporte un risque de perte en capital. Consultez un conseiller financier agréé pour des décisions importantes.**
