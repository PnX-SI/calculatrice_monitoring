import { Component, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import * as moment from 'moment';
import { Indicator, Protocol, SitesGroup } from '../../interfaces';
import { DataService } from '../../services/data.service';

interface Campaign {
  startDate: string;
  endDate: string;
}

interface SitesGroupChoice extends SitesGroup {
  disabled?: boolean;
}

const noOverlappedCampaignsValidator: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const format = 'YYYY-MM-DD';
  const campaigns: Campaign[] = control.value;
  let overlapSpotted = false;
  campaigns.forEach((camp1) => {
    campaigns.forEach((camp2) => {
      if (camp1 !== camp2) {
        const start1 = moment(camp1.startDate, format);
        const end1 = moment(camp1.endDate, format);
        const start2 = moment(camp2.startDate, format);
        const end2 = moment(camp2.endDate, format);
        if (
          !(
            (start1.isBefore(start2) && end1.isBefore(start2)) ||
            (start2.isBefore(start1) && end2.isBefore(start1))
          )
        ) {
          overlapSpotted = true;
        }
      }
    });
  });
  return overlapSpotted ? { campaignsOverlap: true } : null;
};

const endAfterStartValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const format = 'YYYY-MM-DD';
  const start = moment(control.value.startDate, format);
  const end = moment(control.value.endDate, format);
  return end.isBefore(start) ? { endIsBeforeStart: true } : null;
};

@Component({
  selector: 'pnx-calc-viz-params-form',
  templateUrl: './visualization-params-form.component.html',
  styleUrls: ['./visualization-params-form.component.css'],
})
export class VisualizationParamsFormComponent implements OnInit {
  campaignForm: FormGroup;
  sitesGroupChoices: Array<SitesGroupChoice> = undefined;
  private sitesGroups: Array<SitesGroup> = undefined;
  private protocolCode: string = undefined;

  constructor(
    private _formBuilder: FormBuilder,
    private _data: DataService,
    private _router: Router,
    private _route: ActivatedRoute
  ) {
    this.campaignForm = this._formBuilder.group({
      sitesGroup: [null, Validators.required],
      campaigns: this._formBuilder.array([], { validators: noOverlappedCampaignsValidator }),
    });
  }

  ngOnInit(): void {
    this._route.params.subscribe((params) => {
      this._data.getIndicator(params.indicatorId).subscribe((indicator: Indicator) => {
        this._data.getProtocol(indicator.protocolId).subscribe((protocol: Protocol) => {
          this.protocolCode = protocol.code;
          this._data.getSitesGroups(this.protocolCode).subscribe((data: Array<SitesGroup>) => {
            this.sitesGroups = data;
            this.sitesGroupChoices = this.getSitesGroupChoices(data);
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
    return this._formBuilder.group(
      {
        startDate: ['', Validators.required],
        endDate: ['', Validators.required],
      },
      { validators: endAfterStartValidator }
    );
  }

  /**
   * Ajoute une nouvelle campagne au FormArray.
   */
  addCampaign() {
    let newCampaign = this.newCampaign();
    this.campaigns.push(newCampaign);
    const nbCampaigns = this.campaigns.value.length;
    if (nbCampaigns > 1) {
      const previousCampaign: Campaign = this.campaigns.value[nbCampaigns - 2];
      const newCampaignStart = this.getNextDay(previousCampaign.endDate);
      newCampaign.patchValue({
        startDate: newCampaignStart,
        endDate: this.getNextYear(newCampaignStart),
      });
    }
  }

  /**
   * Supprime une campagne à un index spécifique.
   */
  removeCampaign(campaignIndex: number) {
    this.campaigns.removeAt(campaignIndex);
  }

  onStartDateChange(campaignForm: FormControl) {
    if (!campaignForm.value.endDate) {
      campaignForm.patchValue({ endDate: this.getNextYear(campaignForm.value.startDate) });
    }
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
            state: {
              sites: sites,
              campaigns: this.campaignForm.value.campaigns,
            },
          });
        });
    } else {
      console.error('Le formulaire contient des erreurs.');
    }
  }

  private getNextDay(date: string) {
    const format = 'YYYY-MM-DD';
    const dateObj = moment(date, format);
    return dateObj.add(1, 'day').format(format);
  }

  private getNextYear(date: string) {
    const format = 'YYYY-MM-DD';
    const dateObj = moment(date, format);
    return dateObj.add(1, 'year').subtract(1, 'day').format(format);
  }

  private getSitesGroupChoices(sitesGroups: SitesGroup[]) {
    return sitesGroups.map<SitesGroupChoice>((group) => {
      let groupChoice: SitesGroupChoice = structuredClone(group);
      groupChoice.disabled = group.nbSites === 0;
      if (groupChoice.disabled) groupChoice.name = `${groupChoice.name} (aucun site)`;
      return groupChoice;
    });
  }
}
