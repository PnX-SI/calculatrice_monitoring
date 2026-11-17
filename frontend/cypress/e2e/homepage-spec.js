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

  it('should display 4 indicator items', () => {
    cy.visit('/#/calculatrice');
    cy.get('.indic-list mat-list-item a').its('length').should('eq', 4);
    cy.get('.indic-list mat-list-item a')
      .first()
      .invoke('text')
      .should('contain', "I02 - indice floristique d'engorgement");
  });

  it('allows to reach the chosen indicator viz param form', () => {
    cy.visit('/#/calculatrice');
    cy.get('.indic-list mat-list-item a').its('length').should('eq', 4);
    cy.get('.indic-list mat-list-item a').first().click();
    cy.get('pnx-calc-viz-params-form').should('exist');
    cy.location('hash').should('eq', '#/calculatrice/visualization/1/params');
  });
});
