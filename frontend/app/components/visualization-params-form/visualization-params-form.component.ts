import { Component, OnInit } from '@angular/core';
import { FormArray, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Indicator, Protocol, SitesGroup } from '../../interfaces';
import { DataService } from '../../services/data.service';

interface Campaign {
  startDate: string;
  endDate: string;
}

@Component({
  selector: 'pnx-calc-viz-params-form',
  templateUrl: './visualization-params-form.component.html',
  styleUrls: ['./visualization-params-form.component.css'],
})
export class VisualizationParamsFormComponent implements OnInit {
  campaignForm: FormGroup;
  sitesGroups: Array<SitesGroup> = undefined;
  private protocolCode: string = undefined;

  constructor(
    private _formBuilder: FormBuilder,
    private _data: DataService,
    private _router: Router,
    private _route: ActivatedRoute
  ) {
    this.campaignForm = this._formBuilder.group({
      sitesGroup: [null],
      campaigns: this._formBuilder.array([]),
    });
  }

  ngOnInit(): void {
    this._route.params.subscribe((params) => {
      this._data.getIndicator(params.indicatorId).subscribe((indicator: Indicator) => {
        this._data.getProtocol(indicator.protocolId).subscribe((protocol: Protocol) => {
          this.protocolCode = protocol.code;
          this._data.getSitesGroups(this.protocolCode).subscribe((data: Array<SitesGroup>) => {
            this.sitesGroups = data;
          });
        });
      });
    });
    this.addCampaign();
  }

  /**
   * Getter pratique pour accéder facilement au FormArray depuis le template.
   */
  get campaigns(): FormArray {
    return this.campaignForm.get('campaigns') as FormArray;
  }

  /**
   * Crée un nouveau FormGroup pour une campagne.
   */
  newCampaign(): FormGroup {
    return this._formBuilder.group({
      startDate: ['', Validators.required],
      endDate: ['', Validators.required],
    });
  }

  /**
   * Ajoute une nouvelle campagne au FormArray.
   */
  addCampaign() {
    this.campaigns.push(this.newCampaign());
  }

  /**
   * Supprime une campagne à un index spécifique.
   * @param campaignIndex L'index de la campagne à supprimer.
   */
  removeCampaign(campaignIndex: number) {
    this.campaigns.removeAt(campaignIndex);
  }

  /**
   * Gère la soumission du formulaire.
   */
  onSubmit() {
    if (this.campaignForm.valid) {
      this._data
        .getSites(
          this.protocolCode,
          this.sitesGroups.find((item) => item.id === this.campaignForm.value.sitesGroup)
        )
        .subscribe((sites) => {
          this._router.navigate(['..'], {
            relativeTo: this._route,
            queryParams: {
              sites: sites.map((item) => item.id).join(),
              campaigns: this.getCampaignsParam(this.campaignForm.value.campaigns),
            },
          });
        });
    } else {
      console.error('Le formulaire contient des erreurs.');
    }
  }

  /**
   * Helper : transforme les campagnes saisies dans le formulaire en un texte à passer
   * en query param. Exemple : 20230601-20240531,20240601-20250531
   *
   * @param campaigns Les valeurs du FormArray campaigns
   * @private
   */
  private getCampaignsParam(campaigns: Array<Campaign>): string {
    let params = [];
    campaigns.forEach((campaign) => {
      const start = campaign.startDate.replaceAll('-', '');
      const end = campaign.endDate.replaceAll('-', '');
      params.push(`${start}-${end}`);
    });
    return params.join(',');
  }
}
