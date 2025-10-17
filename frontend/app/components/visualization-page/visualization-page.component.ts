import { Component, OnInit } from '@angular/core';
import { MatListOption } from '@angular/material/list';
import { ActivatedRoute, Router } from '@angular/router';
import { Campaign, Site, VisualizationBlockDefinition } from '../../interfaces';
import { DataService } from '../../services/data.service';

interface Selection {
  label: string;
  type: 'synthese' | 'campaign' | 'evolution';
  campaigns: Campaign[];
}

@Component({
  selector: 'pnx-calc-visualization-page',
  templateUrl: './visualization-page.component.html',
  styleUrls: ['./visualization-page.component.css'],
})
export class VisualizationPageComponent implements OnInit {
  protected vizBlocks: VisualizationBlockDefinition[];
  protected selections: Selection[];
  private _sites: Site[];
  private _campaigns: Campaign[];
  private _indicatorId: number;

  constructor(
    private _data: DataService,
    private _router: Router,
    private _route: ActivatedRoute
  ) {}

  ngOnInit() {
    this._sites = window.history.state.sites;
    this._campaigns = window.history.state.campaigns;
    if (this._sites === undefined || this._campaigns === undefined) {
      this._router.navigate(['./params'], {
        relativeTo: this._route,
      });
    }
    this.selections = this._buildSelections(this._campaigns);
    this._route.params.subscribe((params) => {
      this._indicatorId = params.indicatorId;
      const firstSelection = this.selections[0];
      // The first selection is also visually selected in the template.
      this._updateVisualization(firstSelection);
    });
  }

  onSelectionsChange(items: MatListOption[]) {
    // The selection list is configured to allow single item selection only.
    let selection: Selection = items[0].value;
    this._updateVisualization(selection);
  }

  private _buildSelections(campaigns: Campaign[]): Selection[] {
    let selections: Selection[] = [];
    if (campaigns.length > 1) {
      selections.push({
        label: 'Synthèse',
        type: 'synthese',
        campaigns: campaigns,
      });
    }
    let previousCampaign = undefined;
    campaigns.forEach((campaign) => {
      if (previousCampaign !== undefined) {
        selections.push({
          label: `Évolution`,
          type: 'evolution',
          campaigns: [previousCampaign, campaign],
        });
      }
      selections.push({
        label: `Campagne ${campaign.startDate}-${campaign.endDate}`,
        type: 'campaign',
        campaigns: [campaign],
      });
      previousCampaign = campaign;
    });
    return selections;
  }

  private _updateVisualization(vizSelection: Selection) {
    this._data
      .getVisualizationBlocks(
        this._indicatorId,
        this._sites,
        vizSelection.campaigns,
        vizSelection.type
      )
      .subscribe((data) => {
        this.vizBlocks = data;
      });
  }
}
