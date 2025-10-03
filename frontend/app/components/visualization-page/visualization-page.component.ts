import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'pnx-calc-visualization-page',
  template: `
    <p>Sites: {{ sites | json }}</p>
    <p>Campaigns: {{ campaigns | json }}</p>
  `,
})
export class VisualizationPageComponent implements OnInit {
  sites: string;
  campaigns: string;

  ngOnInit() {
    this.sites = window.history.state.sites;
    this.campaigns = window.history.state.campaigns;
  }
}
