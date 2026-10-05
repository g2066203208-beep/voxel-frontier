# T038-S1 method-source entry: RNA mass, eccentricity and inertia

Source: Cheng Y. et al., Structures 68 (2024) 107235, DOI [10.1016/j.istruc.2024.107235](https://doi.org/10.1016/j.istruc.2024.107235), REF010/L059.

This audit directly read relevant PDF pages 3–9 and visually inspected pages 3, 5–9. It does not claim a complete new scientific audit of all 12 pages or a reproduction of the authors’ calculations.

|Locator|Published method|Use and limit for T038-S1|
|---|---|---|
|p.3 §2.1/Fig.2; pp.4–5 Eqs.(13)–(30)|RNA mass, eccentric reference positions and rotational inertia enter the structural dynamic formulation.|Supports preserving these distinct quantities; does not provide the current full 6×6 operator.|
|pp.6–7 §4.1; p.7 Fig.5|The principal FE model places concentrated mass/inertia at separate nacelle/rotor reference points and couples them to the tower-top section. Fig.5 identifies rigid kinematic coupling.|Provides a published modelling precedent. The paper does not disclose MASS/ROTARYI keywords or the current single-CG-to-single-tower-top-node deck.|
|p.7 §5.1; p.9 Fig.7/Table4|PM, EPM, EPMJ and EDPMJ alternatives are compared; EPMJ retains a single eccentric mass and rotational inertia.|The current representation is conceptually closest to EPMJ; its complete 3D tensor and implementation still require their own definitions and checks.|
|pp.7–8 §4.1–4.2/Table3/Fig.6|Prestress is established before modal extraction; analytical and FE frequencies and mode shapes are compared in both lateral directions.|This is a tower modal comparison with simplified RNA, not flexible rotating aeroelastic validation or an isolated matrix/energy/gravity fixture.|

The paper is not a source for current R2 numerical properties, off-diagonal inertia inputs, solver mass-matrix extraction, or the S1 test duration, amplitudes and tolerances. Exact keyword behaviour must be supported by the separately checked Abaqus documentation; the M6 transformation and isolated tests must be labelled as project derivation and numerical implementation verification. T026 M11/M12 already distinguish these roles. No numerical check of this rigid operator can by itself close the flexible-RNA applicability question D08.

Only original summaries and bibliographic locators are provided here. PDF pages, extracted full text, private paths and private manuscript/advisor materials are excluded. This entry was prepared locally and was not published by this reviewer.
