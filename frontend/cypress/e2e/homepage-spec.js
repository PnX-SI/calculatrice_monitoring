const SELECTOR_SIDEBAR_HOME_BUTTON = '[data-qa="gn-sidenav-mat-card"]';
const SELECTOR_HOME_CONTENT = '[data-qa="pnx-home-content"]';
const SELECTOR_CALCULATRICE_LINK = '[data-qa="gn-sidenav-link-CALCULATRICE"]';

describe('Testing homepage', () => {
  beforeEach(() => {
    cy.geonatureLogin();
    cy.visit('/#/');
  });

  it('should display calculatrice home page and go back to home', () => {
    cy.get(SELECTOR_HOME_CONTENT).should('exist').should('be.visible');
    cy.get(SELECTOR_CALCULATRICE_LINK).click({ force: true });
    cy.url().should('include', 'calculatrice');
    cy.get(SELECTOR_SIDEBAR_HOME_BUTTON).click();
    cy.get(SELECTOR_HOME_CONTENT).should('exist').should('be.visible');
  });

  it('should have an appropriate page title', () => {
    cy.visit('/#/calculatrice');
    cy.title().should('eq', 'GeoNature2 - Calculatrice');
  });
});
